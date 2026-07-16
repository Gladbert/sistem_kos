from datetime import date, datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from extensions import db
from models import User, Room, Booking, Payment, Notification

onboarding_bp = Blueprint("onboarding", __name__, url_prefix="/onboarding")


@onboarding_bp.route("/")
def index():
    rooms = Room.query.filter_by(status="tersedia").order_by(Room.lantai, Room.nomor_kamar).all()
    return render_template("onboarding/index.html", rooms=rooms)


@onboarding_bp.route("/kamar")
def lihat_kamar():
    rooms = Room.query.filter_by(status="tersedia").order_by(Room.harga_per_bulan).all()
    return render_template("onboarding/kamar.html", rooms=rooms)


@onboarding_bp.route("/kamar/<int:id>")
def detail_kamar(id):
    room = Room.query.get_or_404(id)
    return render_template("onboarding/detail_kamar.html", room=room)


@onboarding_bp.route("/daftar/<int:room_id>", methods=["GET", "POST"])
def daftar(room_id):
    room = Room.query.get_or_404(room_id)

    if room.status != "tersedia":
        flash("Kamar sudah tidak tersedia.", "warning")
        return redirect(url_for("onboarding.index"))

    if request.method == "POST":
        if not current_user.is_authenticated:
            flash("Silakan login atau daftar terlebih dahulu.", "warning")
            return redirect(url_for("auth.login", next=url_for("onboarding.daftar", room_id=room_id)))

        if current_user.role not in ("client",):
            flash("Hanya client yang bisa melakukan booking.", "danger")
            return redirect(url_for("dashboard.index"))

        tanggal_masuk = request.form.get("tanggal_masuk")
        durasi = request.form.get("durasi", 1, type=int)
        deposit_catatan = request.form.get("deposit_catatan", "")

        if not tanggal_masuk:
            flash("Tanggal masuk wajib diisi.", "danger")
            return render_template("onboarding/daftar.html", room=room)

        try:
            tgl_masuk = datetime.strptime(tanggal_masuk, "%Y-%m-%d").date()
        except ValueError:
            flash("Format tanggal salah.", "danger")
            return render_template("onboarding/daftar.html", room=room)

        from dateutil.relativedelta import relativedelta
        try:
            tgl_keluar = tgl_masuk + relativedelta(months=durasi)
        except ImportError:
            tgl_keluar = date(tgl_masuk.year + (tgl_masuk.month + durasi - 1) // 12,
                             (tgl_masuk.month + durasi - 1) % 12 + 1, tgl_masuk.day)

        booking = Booking(
            user_id=current_user.id,
            room_id=room.id,
            tanggal_masuk=tgl_masuk,
            tanggal_keluar=tgl_keluar,
            status="aktif",
            deposit=room.harga_per_bulan,
            catatan=deposit_catatan,
        )
        room.status = "terisi"
        db.session.add(booking)
        db.session.commit()

        notif = Notification(
            user_id=current_user.id,
            pesan=f"Selamat! Kamar {room.nomor_kamar} berhasil dipesan. Check-in: {tgl_masuk.strftime('%d/%m/%Y')}.",
            jenis="umum",
        )
        db.session.add(notif)
        db.session.commit()

        flash(f"Selamat! Kamar {room.nomor_kamar} berhasil dipesan.", "success")
        return redirect(url_for("dashboard.client"))

    return render_template("onboarding/daftar.html", room=room)
