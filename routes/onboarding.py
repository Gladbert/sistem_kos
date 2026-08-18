from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, session, current_app
from flask_login import login_required, current_user
from extensions import db
from models import User, Room, Booking, Payment, Notification, compute_keluar, DEFAULT_STAY_UNITS
from helpers import create_notification, get_or_404, safe_commit

onboarding_bp = Blueprint("onboarding", __name__, url_prefix="/onboarding")


def _available_rooms():
    query = Room.query.filter_by(status="tersedia")
    kos_id = session.get("kos_id")
    if kos_id:
        query = query.filter_by(kos_id=kos_id)
    return query


@onboarding_bp.route("/")
def index():
    rooms = _available_rooms().order_by(Room.lantai, Room.nomor_kamar).all()
    return render_template("onboarding/index.html", rooms=rooms)


@onboarding_bp.route("/kamar")
def lihat_kamar():
    rooms = _available_rooms().order_by(Room.harga_per_bulan).all()
    # All types from DB for filter dropdown (even if no available rooms of that type)
    kos_id = session.get("kos_id")
    type_query = db.session.query(Room.tipe).distinct()
    if kos_id:
        type_query = type_query.filter_by(kos_id=kos_id)
    all_types = sorted([t[0] for t in type_query.all()])
    return render_template("onboarding/kamar.html", rooms=rooms, all_types=all_types)


@onboarding_bp.route("/kamar/<int:id>")
def detail_kamar(id):
    room = get_or_404(Room, id)
    return render_template("onboarding/detail_kamar.html", room=room)


@onboarding_bp.route("/daftar/<int:room_id>", methods=["GET", "POST"])
def daftar(room_id):
    room = get_or_404(Room, room_id)

    # kos default stay preset — used to prefill the duration fields
    default_value = room.kos.default_stay_value if room.kos else 1
    default_unit = room.kos.default_stay_unit if room.kos else "bulan"

    if room.status != "tersedia":
        flash("Kamar sudah tidak tersedia.", "warning")
        return redirect(url_for("onboarding.index"))

    def render_form():
        return render_template("onboarding/daftar.html", room=room, default_value=default_value, default_unit=default_unit)

    if request.method == "POST":
        if not current_user.is_authenticated:
            flash("Silakan login atau daftar terlebih dahulu.", "warning")
            return redirect(url_for("auth.login", next=url_for("onboarding.daftar", room_id=room_id)))

        if current_user.role not in ("client",):
            flash("Hanya client yang bisa melakukan booking.", "danger")
            return redirect(url_for("dashboard.index"))

        # Check if client already has active booking for this room
        existing = Booking.query.filter_by(
            user_id=current_user.id, room_id=room.id
        ).filter(Booking.status.in_(["pending", "approved", "aktif"])).first()
        if existing:
            flash(f"Anda sudah memiliki booking aktif untuk kamar {room.nomor_kamar}.", "warning")
            return redirect(url_for("dashboard.client"))

        tanggal_masuk = request.form.get("tanggal_masuk")
        durasi_value = request.form.get("durasi_value", type=int)
        durasi_unit = request.form.get("durasi_unit", "bulan")
        deposit_catatan = request.form.get("deposit_catatan", "")

        if not tanggal_masuk:
            flash("Tanggal masuk wajib diisi.", "danger")
            return render_form()

        try:
            tgl_masuk = datetime.strptime(tanggal_masuk, "%Y-%m-%d").date()
        except ValueError:
            flash("Format tanggal salah.", "danger")
            return render_form()

        if not durasi_value or durasi_value < 1:
            flash("Durasi sewa minimal 1.", "danger")
            return render_form()
        if durasi_unit not in DEFAULT_STAY_UNITS:
            flash("Satuan durasi tidak valid.", "danger")
            return render_form()

        tgl_keluar = compute_keluar(tgl_masuk, durasi_value, durasi_unit)

        booking = Booking(
            user_id=current_user.id,
            room_id=room.id,
            tanggal_masuk=tgl_masuk,
            tanggal_keluar=tgl_keluar,
            status="pending",
            deposit=room.harga_per_bulan,
            catatan=deposit_catatan,
        )
        db.session.add(booking)
        try:
            safe_commit()
        except Exception:
            current_app.logger.exception("Database operation failed")
            db.session.rollback()
            flash("Terjadi kesalahan saat menyimpan data.", "danger")
            return redirect(request.referrer or url_for("dashboard.index"))

        create_notification(
            current_user.id,
            f"Permintaan sewa kamar {room.nomor_kamar} telah dikirim. Menunggu persetujuan pengelola.",
        )

        # Notify admin
        admins = User.query.filter(User.role.in_(["admin", "management"])).all()
        for a in admins:
            db.session.add(Notification(
                user_id=a.id,
                pesan=f"Permintaan booking baru dari {current_user.nama_lengkap} untuk kamar {room.nomor_kamar}.",
                jenis="umum",
            ))
        try:
            safe_commit()
        except Exception:
            current_app.logger.exception("Database operation failed")
            db.session.rollback()
            flash("Terjadi kesalahan saat menyimpan data.", "danger")
            return redirect(request.referrer or url_for("dashboard.index"))

        flash(f"Permintaan sewa kamar {room.nomor_kamar} telah dikirim. Menunggu persetujuan pengelola.", "success")
        return redirect(url_for("dashboard.client"))

    return render_form()
