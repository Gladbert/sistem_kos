from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, session
from flask_login import login_required, current_user
from extensions import db
from sqlalchemy import or_
from sqlalchemy.orm import joinedload
from models import User, Booking, Payment, Notification, Room
from helpers import admin_or_management, get_or_404, kos_room_ids, kos_rooms, safe_commit, require_module_perm

clients_bp = Blueprint("clients", __name__, url_prefix="/clients")


@clients_bp.route("/")
@admin_or_management
def index():
    page = request.args.get("page", 1, type=int)
    per_page = 20
    search = request.args.get("search", "").strip()
    query = User.query.filter_by(role="client")

    if search:
        query = query.filter(
            or_(
                User.nama_lengkap.ilike(f"%{search}%"),
                User.username.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%"),
                User.no_telepon.ilike(f"%{search}%"),
            )
        )

    pagination = query.order_by(User.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    room_ids = kos_room_ids()
    aktif_q = Booking.query.filter_by(status="aktif")
    if room_ids:
        aktif_q = aktif_q.filter(Booking.room_id.in_(room_ids))
    aktif_ids = [b.user_id for b in aktif_q.all()]

    return render_template("clients/index.html", pagination=pagination, clients=pagination.items, aktif_ids=aktif_ids)


@clients_bp.route("/<int:id>")
@login_required
def detail(id):
    if current_user.role not in ("admin", "management") and current_user.id != id:
        flash("Akses ditolak.", "danger")
        return redirect(url_for("dashboard.index"))

    client = get_or_404(User, id)
    booking_aktif = Booking.query.options(
        joinedload(Booking.room)
    ).filter_by(user_id=id, status="aktif").first()
    bookings = Booking.query.options(
        joinedload(Booking.room)
    ).filter_by(user_id=id).order_by(Booking.created_at.desc()).all()
    payments = Payment.query.options(
        joinedload(Payment.booking).joinedload(Booking.room)
    ).join(Booking).filter(
        Booking.user_id == id
    ).order_by(Payment.created_at.desc()).all()

    return render_template("clients/detail.html", client=client, bookings=bookings, payments=payments, booking_aktif=booking_aktif)


@clients_bp.route("/nonaktifkan/<int:id>", methods=["POST"])
@admin_or_management
def nonaktifkan(id):
    if not require_module_perm("clients", "edit"):
        return redirect(url_for("dashboard.index"))
    user = get_or_404(User, id)
    user.is_active = not user.is_active
    try:
        safe_commit()
    except Exception:
        current_app.logger.exception("Database operation failed")
        db.session.rollback()
        flash("Terjadi kesalahan saat menyimpan data.", "danger")
        return redirect(request.referrer or url_for("dashboard.index"))
    status = "diaktifkan" if user.is_active else "dinonaktifkan"
    flash(f"Akun {user.nama_lengkap} berhasil {status}.", "success")
    return redirect(url_for("clients.index"))


@clients_bp.route("/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit(id):
    is_admin = current_user.role in ("admin", "management")
    # Admin/management: full access. Resident: self-service (password only).
    if not is_admin and current_user.id != id:
        flash("Akses ditolak.", "danger")
        return redirect(url_for("clients.index"))
    client = get_or_404(User, id)
    if is_admin and not require_module_perm("clients", "edit"):
        return redirect(url_for("dashboard.index"))

    booking_aktif = Booking.query.filter_by(user_id=id, status="aktif").first() if is_admin else None
    rooms = kos_rooms() if is_admin else []

    if request.method == "POST":
        if is_admin:
            # Full profile: name, contact, address (admin/management only)
            client.nama_lengkap = request.form.get("nama_lengkap", client.nama_lengkap)
            email = request.form.get("email", client.email).strip()
            if not email or "@" not in email:
                flash("Email tidak valid.", "danger")
                return render_template("clients/edit.html", client=client, booking_aktif=booking_aktif, rooms=rooms)
            dup = User.query.filter(User.email == email, User.id != client.id).first()
            if dup:
                flash("Email sudah digunakan penghuni lain.", "danger")
                return render_template("clients/edit.html", client=client, booking_aktif=booking_aktif, rooms=rooms)
            client.email = email
            client.no_telepon = request.form.get("no_telepon")
            client.alamat = request.form.get("alamat")

            # Reassign room: update booking.room_id FK, atomic with profile save
            new_room_id = request.form.get("room_id", type=int)
            if booking_aktif and new_room_id and new_room_id != booking_aktif.room_id:
                new_room = db.session.get(Room, new_room_id)
                if new_room and new_room.kos_id == (session.get("kos_id") or new_room.kos_id):
                    old_room = booking_aktif.room
                    booking_aktif.room_id = new_room_id
                    if old_room and old_room.id != new_room_id:
                        other = Booking.query.filter(
                            Booking.room_id == old_room.id, Booking.status == "aktif",
                            Booking.id != booking_aktif.id).first()
                        if not other:
                            old_room.status = "tersedia"
                    new_room.status = "terisi"
                else:
                    flash("Kamar tujuan tidak valid.", "danger")
                    return render_template("clients/edit.html", client=client, booking_aktif=booking_aktif, rooms=rooms)

        # Password (admin and resident self-service)
        password = request.form.get("password", "")
        if password:
            if request.form.get("confirm_password") != password:
                flash("Konfirmasi password tidak cocok.", "danger")
                return render_template("clients/edit.html", client=client, booking_aktif=booking_aktif, rooms=rooms)
            if len(password) < 6:
                flash("Password minimal 6 karakter.", "danger")
                return render_template("clients/edit.html", client=client, booking_aktif=booking_aktif, rooms=rooms)
            client.set_password(password)

        try:
            safe_commit()
        except Exception:
            current_app.logger.exception("Database operation failed")
            db.session.rollback()
            flash("Terjadi kesalahan saat menyimpan data.", "danger")
            return redirect(request.referrer or url_for("dashboard.index"))
        flash(f"Data {client.nama_lengkap} berhasil diperbarui.", "success")
        return redirect(url_for("clients.detail", id=id))

    return render_template("clients/edit.html", client=client, booking_aktif=booking_aktif, rooms=rooms)
