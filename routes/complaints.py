from flask import Blueprint, render_template, request, redirect, flash, url_for
from flask_login import login_required, current_user
from extensions import db
from models import Complaint
from helpers import log_activity

complaint_bp = Blueprint("complaints", __name__, url_prefix="/komplain")


@complaint_bp.route("/")
@login_required
def index():
    if current_user.role in ("admin", "management"):
        c = Complaint.query.order_by(Complaint.created_at.desc()).all()
    else:
        c = Complaint.query.filter_by(user_id=current_user.id).order_by(Complaint.created_at.desc()).all()
    return render_template("complaints/index.html", complaints=c)


@complaint_bp.route("/tambah", methods=["GET", "POST"])
@login_required
def create():
    if request.method == "POST":
        c = Complaint(
            user_id=current_user.id, judul=request.form["judul"],
            deskripsi=request.form["deskripsi"],
            kategori=request.form.get("kategori", "umum")
        )
        db.session.add(c)
        log_activity(current_user.id, "Buat komplain", f"Judul: {request.form['judul']}", "Complaint")
        db.session.commit()
        flash("Komplain terkirim.", "success")
        return redirect(url_for("complaints.index"))
    return render_template("complaints/form.html")


@complaint_bp.route("/tanggap/<int:id>", methods=["POST"])
@login_required
def respond(id):
    if current_user.role not in ("admin", "management"):
        flash("Akses ditolak.", "danger")
        return redirect(url_for("complaints.index"))
    c = Complaint.query.get_or_404(id)
    c.tanggapan = request.form["tanggapan"]
    c.status = request.form.get("status", "ditindaklanjuti")
    c.ditanggapi_oleh = current_user.id
    log_activity(current_user.id, "Tanggapi komplain", f"Judul: {c.judul}, Status: {c.status}", "Complaint")
    db.session.commit()
    flash("Tanggapan dikirim.", "success")
    return redirect(url_for("complaints.index"))
