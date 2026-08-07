from flask import Blueprint, render_template, redirect, url_for, flash, request, session, current_app
from flask_login import login_required, current_user
from extensions import db
from models import Room, Booking, MaintenanceRequest, Kos
from helpers import admin_or_management, get_or_404, parse_amount, safe_commit

rooms_bp = Blueprint("rooms", __name__, url_prefix="/rooms")


@rooms_bp.route("/")
@login_required
def index():
    page = request.args.get("page", 1, type=int)
    per_page = 20
    kos_id = session.get("kos_id")
    if current_user.role in ("admin", "management"):
        lantai = request.args.get("lantai", type=int)
        status = request.args.get("status")
        query = Room.query
        if kos_id:
            query = query.filter_by(kos_id=kos_id)
        if lantai:
            query = query.filter_by(lantai=lantai)
        if status:
            query = query.filter_by(status=status)
        pagination = query.order_by(Room.lantai, Room.nomor_kamar).paginate(page=page, per_page=per_page, error_out=False)
        return render_template("rooms/index.html", pagination=pagination, rooms=pagination.items)
    query = Room.query.filter_by(status="tersedia")
    if kos_id:
        query = query.filter_by(kos_id=kos_id)
    pagination = query.order_by(Room.lantai, Room.nomor_kamar).paginate(page=page, per_page=per_page, error_out=False)
    return render_template("rooms/public.html", pagination=pagination, rooms=pagination.items)


@rooms_bp.route("/tambah", methods=["GET", "POST"])
@admin_or_management
def tambah():
    if request.method == "POST":
        nomor = request.form.get("nomor_kamar", "").strip()
        if not nomor:
            flash("Nomor kamar wajib diisi.", "danger")
            return render_template("rooms/form.html")

        kos_id = session.get("kos_id")
        existing = Room.query.filter_by(nomor_kamar=nomor, kos_id=kos_id).first()
        if existing:
            flash("Nomor kamar sudah ada di kos ini.", "danger")
            return render_template("rooms/form.html")

        harga, err = parse_amount(request.form.get("harga_per_bulan"), label="Harga")
        if err:
            flash(err, "danger")
            return render_template("rooms/form.html")

        room = Room(
            kos_id=kos_id,
            nomor_kamar=nomor,
            lantai=int(request.form.get("lantai", 1)),
            tipe=request.form.get("tipe", "Reguler"),
            harga_per_bulan=harga,
            ukuran=request.form.get("ukuran"),
            fasilitas=request.form.get("fasilitas"),
            status=request.form.get("status", "tersedia"),
            deskripsi=request.form.get("deskripsi"),
        )
        db.session.add(room)
        try:
            safe_commit()
        except Exception:
            current_app.logger.exception("Database operation failed")
            db.session.rollback()
            flash("Terjadi kesalahan saat menyimpan data.", "danger")
            return redirect(request.referrer or url_for("dashboard.index"))
        flash(f"Kamar {nomor} berhasil ditambahkan.", "success")
        return redirect(url_for("rooms.index"))

    return render_template("rooms/form.html", room=None)


@rooms_bp.route("/edit/<int:id>", methods=["GET", "POST"])
@admin_or_management
def edit(id):
    room = get_or_404(Room, id)

    if request.method == "POST":
        nomor = request.form.get("nomor_kamar", "").strip()
        if not nomor:
            flash("Nomor kamar wajib diisi.", "danger")
            return render_template("rooms/form.html", room=room)

        kos_id = session.get("kos_id")
        dup = Room.query.filter_by(nomor_kamar=nomor, kos_id=kos_id).first()
        if dup and dup.id != id:
            flash("Nomor kamar sudah ada di kos ini.", "danger")
            return render_template("rooms/form.html", room=room)

        harga, err = parse_amount(request.form.get("harga_per_bulan"), label="Harga")
        if err:
            flash(err, "danger")
            return render_template("rooms/form.html", room=room)

        room.nomor_kamar = nomor
        room.lantai = int(request.form.get("lantai", 1))
        room.tipe = request.form.get("tipe", "Reguler")
        room.harga_per_bulan = harga
        room.ukuran = request.form.get("ukuran")
        room.fasilitas = request.form.get("fasilitas")
        room.status = request.form.get("status", "tersedia")
        room.deskripsi = request.form.get("deskripsi")
        try:
            safe_commit()
        except Exception:
            current_app.logger.exception("Database operation failed")
            db.session.rollback()
            flash("Terjadi kesalahan saat menyimpan data.", "danger")
            return redirect(request.referrer or url_for("dashboard.index"))
        flash(f"Kamar {nomor} berhasil diperbarui.", "success")
        return redirect(url_for("rooms.index"))

    return render_template("rooms/form.html", room=room)


@rooms_bp.route("/hapus/<int:id>", methods=["POST"])
@admin_or_management
def hapus(id):
    room = get_or_404(Room, id)
    if room.status == "terisi":
        flash("Kamar sedang terisi, tidak bisa dihapus.", "danger")
        return redirect(url_for("rooms.index"))

    db.session.delete(room)
    try:
        safe_commit()
    except Exception:
        current_app.logger.exception("Database operation failed")
        db.session.rollback()
        flash("Terjadi kesalahan saat menyimpan data.", "danger")
        return redirect(request.referrer or url_for("dashboard.index"))
    flash(f"Kamar {room.nomor_kamar} berhasil dihapus.", "success")
    return redirect(url_for("rooms.index"))


@rooms_bp.route("/<int:id>")
@login_required
def detail(id):
    room = get_or_404(Room, id)
    booking = room.booking_aktif
    maintenance = MaintenanceRequest.query.filter_by(room_id=id).order_by(MaintenanceRequest.created_at.desc()).all()
    return render_template("rooms/detail.html", room=room, booking=booking, maintenance=maintenance)
