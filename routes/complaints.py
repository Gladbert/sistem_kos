from flask import Blueprint, render_template, request, redirect, flash, url_for, session, current_app
from flask_login import login_required, current_user
from extensions import db
from models import Complaint, User
from helpers import log_activity, admin_or_management, get_or_404, safe_commit
from sqlalchemy.orm import joinedload

complaint_bp = Blueprint("complaints", __name__, url_prefix="/komplain")


@complaint_bp.route("/")
@login_required
def index():
    page = request.args.get("page", 1, type=int)
    per_page = 20
    kos_id = session.get("kos_id")
    if current_user.role in ("admin", "management"):
        q = Complaint.query.options(
            joinedload(Complaint.user), joinedload(Complaint.responder)
        )
        if kos_id:
            q = q.filter(Complaint.kos_id == kos_id)
        pagination = q.order_by(Complaint.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    else:
        pagination = Complaint.query.filter_by(user_id=current_user.id).order_by(Complaint.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return render_template("complaints/index.html", pagination=pagination, complaints=pagination.items)


@complaint_bp.route("/tambah", methods=["GET", "POST"])
@login_required
def create():
    if request.method == "POST":
        c = Complaint(
            user_id=current_user.id,
            kos_id=session.get("kos_id"),
            judul=request.form["judul"],
            deskripsi=request.form["deskripsi"],
            kategori=request.form.get("kategori", "umum"),
        )
        db.session.add(c)
        log_activity(current_user.id, "Buat komplain", f"Judul: {request.form['judul']}", "Complaint")
        try:
            safe_commit()
        except Exception:
            current_app.logger.exception("Database operation failed")
            db.session.rollback()
            flash("Terjadi kesalahan saat menyimpan data.", "danger")
            return redirect(request.referrer or url_for("dashboard.index"))
        flash("Komplain terkirim.", "success")
        return redirect(url_for("complaints.index"))
    return render_template("complaints/form.html")


@complaint_bp.route("/tanggap/<int:id>", methods=["POST"])
@admin_or_management
def respond(id):
    c = get_or_404(Complaint, id)
    c.tanggapan = request.form["tanggapan"]
    c.status = request.form.get("status", "ditindaklanjuti")
    c.ditanggapi_oleh = current_user.id
    log_activity(current_user.id, "Tanggapi komplain", f"Judul: {c.judul}, Status: {c.status}", "Complaint")
    try:
        safe_commit()
    except Exception:
        current_app.logger.exception("Database operation failed")
        db.session.rollback()
        flash("Terjadi kesalahan saat menyimpan data.", "danger")
        return redirect(request.referrer or url_for("dashboard.index"))
    flash("Tanggapan dikirim.", "success")
    return redirect(url_for("complaints.index"))
