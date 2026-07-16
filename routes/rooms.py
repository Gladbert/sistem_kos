from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from extensions import db
from models import Room, Booking

rooms_bp = Blueprint("rooms", __name__, url_prefix="/rooms")


@rooms_bp.route("/")
@login_required
def index():
    if current_user.role == "admin":
        lantai = request.args.get("lantai", type=int)
        status = request.args.get("status")
        query = Room.query
        if lantai:
            query = query.filter_by(lantai=lantai)
        if status:
            query = query.filter_by(status=status)
        rooms = query.order_by(Room.lantai, Room.nomor_kamar).all()
        return render_template("rooms/index.html", rooms=rooms)
    rooms = Room.query.filter_by(status="tersedia").order_by(Room.lantai, Room.nomor_kamar).all()
    return render_template("rooms/public.html", rooms=rooms)


@rooms_bp.route("/tambah", methods=["GET", "POST"])
@login_required
def tambah():
    if current_user.role not in ("admin", "management"):
        flash("Akses ditolak.", "danger")
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        nomor = request.form.get("nomor_kamar", "").strip()
        if not nomor:
            flash("Nomor kamar wajib diisi.", "danger")
            return render_template("rooms/form.html")

        if Room.query.filter_by(nomor_kamar=nomor).first():
            flash("Nomor kamar sudah ada.", "danger")
            return render_template("rooms/form.html")

        try:
            harga = float(request.form.get("harga_per_bulan", 0))
        except ValueError:
            flash("Harga harus angka.", "danger")
            return render_template("rooms/form.html")

        room = Room(
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
        db.session.commit()
        flash(f"Kamar {nomor} berhasil ditambahkan.", "success")
        return redirect(url_for("rooms.index"))

    return render_template("rooms/form.html", room=None)


@rooms_bp.route("/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit(id):
    if current_user.role not in ("admin", "management"):
        flash("Akses ditolak.", "danger")
        return redirect(url_for("dashboard.index"))

    room = Room.query.get_or_404(id)

    if request.method == "POST":
        nomor = request.form.get("nomor_kamar", "").strip()
        if not nomor:
            flash("Nomor kamar wajib diisi.", "danger")
            return render_template("rooms/form.html", room=room)

        existing = Room.query.filter_by(nomor_kamar=nomor).first()
        if existing and existing.id != id:
            flash("Nomor kamar sudah digunakan.", "danger")
            return render_template("rooms/form.html", room=room)

        try:
            harga = float(request.form.get("harga_per_bulan", 0))
        except ValueError:
            flash("Harga harus angka.", "danger")
            return render_template("rooms/form.html", room=room)

        room.nomor_kamar = nomor
        room.lantai = int(request.form.get("lantai", 1))
        room.tipe = request.form.get("tipe", "Reguler")
        room.harga_per_bulan = harga
        room.ukuran = request.form.get("ukuran")
        room.fasilitas = request.form.get("fasilitas")
        room.status = request.form.get("status", "tersedia")
        room.deskripsi = request.form.get("deskripsi")
        db.session.commit()
        flash(f"Kamar {nomor} berhasil diperbarui.", "success")
        return redirect(url_for("rooms.index"))

    return render_template("rooms/form.html", room=room)


@rooms_bp.route("/hapus/<int:id>", methods=["POST"])
@login_required
def hapus(id):
    if current_user.role not in ("admin", "management"):
        flash("Akses ditolak.", "danger")
        return redirect(url_for("dashboard.index"))

    room = Room.query.get_or_404(id)
    if room.status == "terisi":
        flash("Kamar sedang terisi, tidak bisa dihapus.", "danger")
        return redirect(url_for("rooms.index"))

    db.session.delete(room)
    db.session.commit()
    flash(f"Kamar {room.nomor_kamar} berhasil dihapus.", "success")
    return redirect(url_for("rooms.index"))


@rooms_bp.route("/<int:id>")
@login_required
def detail(id):
    room = Room.query.get_or_404(id)
    booking = room.booking_aktif
    from models import MaintenanceRequest
    maintenance = MaintenanceRequest.query.filter_by(room_id=id).order_by(MaintenanceRequest.created_at.desc()).all()
    return render_template("rooms/detail.html", room=room, booking=booking, maintenance=maintenance)
