from flask import Blueprint, render_template, request, redirect, flash, url_for, current_app
from flask_login import login_required, current_user
from extensions import db
from models import Announcement
from helpers import log_activity, admin_or_management, get_or_404, safe_commit, require_module_perm, sanitize

announcement_bp = Blueprint("announcements", __name__, url_prefix="/pengumuman")


@announcement_bp.route("/")
@login_required
def index():
    page = request.args.get("page", 1, type=int)
    per_page = 20
    if current_user.role in ("admin", "management"):
        pagination = Announcement.query.order_by(Announcement.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    else:
        pagination = Announcement.query.filter_by(ditampilkan=True).order_by(Announcement.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return render_template("announcements/index.html", pagination=pagination, announcements=pagination.items)


@announcement_bp.route("/tambah", methods=["GET", "POST"])
@admin_or_management
def create():
    if not require_module_perm("announcements", "create"):
        return redirect(url_for("dashboard.index"))
    VALID_PRIORITAS = ("normal", "penting", "urgent")
    if request.method == "POST":
        judul = sanitize(request.form.get("judul", "").strip())
        isi = sanitize(request.form.get("isi", "").strip())
        if not judul:
            flash("Judul wajib diisi.", "danger")
            return render_template("announcements/form.html")
        if not isi:
            flash("Isi pengumuman wajib diisi.", "danger")
            return render_template("announcements/form.html")
        prioritas = request.form.get("prioritas", "normal")
        if prioritas not in VALID_PRIORITAS:
            prioritas = "normal"
        a = Announcement(
            judul=judul,
            isi=isi,
            prioritas=prioritas,
            ditampilkan=request.form.get("ditampilkan") == "on",
            created_by=current_user.id,
        )
        db.session.add(a)
        log_activity(current_user.id, "Buat pengumuman", f"Judul: {judul}", "Announcement")
        try:
            safe_commit()
        except Exception:
            current_app.logger.exception("Database operation failed")
            db.session.rollback()
            flash("Terjadi kesalahan saat menyimpan data.", "danger")
            return redirect(request.referrer or url_for("dashboard.index"))
        flash("Pengumuman berhasil dibuat.", "success")
        return redirect(url_for("announcements.index"))
    return render_template("announcements/form.html")


@announcement_bp.route("/edit/<int:id>", methods=["GET", "POST"])
@admin_or_management
def edit(id):
    if not require_module_perm("announcements", "edit"):
        return redirect(url_for("dashboard.index"))
    a = get_or_404(Announcement, id)
    if request.method == "POST":
        judul = sanitize(request.form.get("judul", "").strip())
        isi = sanitize(request.form.get("isi", "").strip())
        if not judul:
            flash("Judul wajib diisi.", "danger")
            return render_template("announcements/form.html", announcement=a)
        if not isi:
            flash("Isi pengumuman wajib diisi.", "danger")
            return render_template("announcements/form.html", announcement=a)
        prioritas = request.form.get("prioritas", "normal")
        if prioritas not in VALID_PRIORITAS:
            prioritas = "normal"
        a.judul = judul
        a.isi = isi
        a.prioritas = prioritas
        a.ditampilkan = request.form.get("ditampilkan") == "on"
        log_activity(current_user.id, "Edit pengumuman", f"Judul: {a.judul}", "Announcement")
        try:
            safe_commit()
        except Exception:
            current_app.logger.exception("Database operation failed")
            db.session.rollback()
            flash("Terjadi kesalahan saat menyimpan data.", "danger")
            return redirect(request.referrer or url_for("dashboard.index"))
        flash("Pengumuman diperbarui.", "success")
        return redirect(url_for("announcements.index"))
    return render_template("announcements/form.html", announcement=a)


@announcement_bp.route("/hapus/<int:id>", methods=["POST"])
@admin_or_management
def delete(id):
    if not require_module_perm("announcements", "delete"):
        return redirect(url_for("dashboard.index"))
    a = get_or_404(Announcement, id)
    log_activity(current_user.id, "Hapus pengumuman", f"Judul: {a.judul}", "Announcement")
    db.session.delete(a)
    try:
        safe_commit()
    except Exception:
        current_app.logger.exception("Database operation failed")
        db.session.rollback()
        flash("Terjadi kesalahan saat menyimpan data.", "danger")
        return redirect(request.referrer or url_for("dashboard.index"))
    flash("Pengumuman dihapus.", "success")
    return redirect(url_for("announcements.index"))
