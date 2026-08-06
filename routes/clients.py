from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from extensions import db
from sqlalchemy import or_
from models import User, Booking, Payment, Notification, Room
from helpers import admin_or_management, get_or_404, kos_room_ids

clients_bp = Blueprint("clients", __name__, url_prefix="/clients")


@clients_bp.route("/")
@admin_or_management
def index():
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

    clients = query.order_by(User.created_at.desc()).all()
    room_ids = kos_room_ids()
    aktif_q = Booking.query.filter_by(status="aktif")
    if room_ids:
        aktif_q = aktif_q.filter(Booking.room_id.in_(room_ids))
    aktif_ids = [b.user_id for b in aktif_q.all()]

    return render_template("clients/index.html", clients=clients, aktif_ids=aktif_ids)


@clients_bp.route("/<int:id>")
@login_required
def detail(id):
    if current_user.role not in ("admin", "management") and current_user.id != id:
        flash("Akses ditolak.", "danger")
        return redirect(url_for("dashboard.index"))

    client = get_or_404(User, id)
    bookings = Booking.query.filter_by(user_id=id).order_by(Booking.created_at.desc()).all()
    payments = Payment.query.join(Booking).filter(
        Booking.user_id == id
    ).order_by(Payment.created_at.desc()).all()

    return render_template("clients/detail.html", client=client, bookings=bookings, payments=payments)


@clients_bp.route("/nonaktifkan/<int:id>", methods=["POST"])
@admin_or_management
def nonaktifkan(id):
    user = get_or_404(User, id)
    user.is_active = not user.is_active
    db.session.commit()
    status = "diaktifkan" if user.is_active else "dinonaktifkan"
    flash(f"Akun {user.nama_lengkap} berhasil {status}.", "success")
    return redirect(url_for("clients.index"))


@clients_bp.route("/edit/<int:id>", methods=["GET", "POST"])
@admin_or_management
def edit(id):
    client = get_or_404(User, id)

    if request.method == "POST":
        client.nama_lengkap = request.form.get("nama_lengkap", client.nama_lengkap)
        client.email = request.form.get("email", client.email)
        client.no_telepon = request.form.get("no_telepon")
        client.alamat = request.form.get("alamat")

        if request.form.get("password"):
            if len(request.form["password"]) >= 6:
                client.set_password(request.form["password"])
            else:
                flash("Password minimal 6 karakter.", "danger")
                return render_template("clients/edit.html", client=client)

        db.session.commit()
        flash(f"Data {client.nama_lengkap} berhasil diperbarui.", "success")
        return redirect(url_for("clients.detail", id=id))

    return render_template("clients/edit.html", client=client)
