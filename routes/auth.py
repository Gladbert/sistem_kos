from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from extensions import db, limiter
from helpers import safe_commit
from models import User

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("10 per minute", methods=["POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            flash("Username dan password wajib diisi.", "danger")
            return render_template("auth/login.html")

        user = User.query.filter_by(username=username).first()

        if not user or not user.check_password(password):
            flash("Username atau password salah.", "danger")
            return render_template("auth/login.html")

        if not user.is_active:
            flash("Akun Anda telah dinonaktifkan.", "danger")
            return render_template("auth/login.html")

        login_user(user, remember=True)
        flash(f"Selamat datang, {user.nama_lengkap}!", "success")

        next_page = request.args.get("next")
        # Prevent open redirect: only allow relative paths
        if next_page and next_page.startswith("/") and not next_page.startswith("//"):
            return redirect(next_page)
        return redirect(url_for("dashboard.index"))

    return render_template("auth/login.html")


@auth_bp.route("/register", methods=["GET", "POST"])
@limiter.limit("5 per minute", methods=["POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")
        nama = request.form.get("nama_lengkap", "").strip()
        telepon = request.form.get("no_telepon", "").strip()
        alamat = request.form.get("alamat", "").strip()

        errors = []
        if not username:
            errors.append("Username wajib diisi.")
        if not email:
            errors.append("Email wajib diisi.")
        if not nama:
            errors.append("Nama lengkap wajib diisi.")
        if not password:
            errors.append("Password wajib diisi.")
        if len(password) < 6:
            errors.append("Password minimal 6 karakter.")
        if password != confirm:
            errors.append("Password tidak cocok.")

        if User.query.filter_by(username=username).first():
            errors.append("Username sudah digunakan.")
        if User.query.filter_by(email=email).first():
            errors.append("Email sudah digunakan.")

        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template("auth/register.html")

        user = User(
            username=username,
            email=email,
            role="client",
            nama_lengkap=nama,
            no_telepon=telepon,
            alamat=alamat,
        )
        user.set_password(password)
        db.session.add(user)
        try:
            safe_commit()
        except Exception:
            current_app.logger.exception("Database operation failed")
            db.session.rollback()
            flash("Terjadi kesalahan saat menyimpan data.", "danger")
            return redirect(request.referrer or url_for("dashboard.index"))

        flash("Pendaftaran berhasil! Silakan login.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Anda telah logout.", "info")
    return redirect(url_for("auth.login"))
