from flask import Blueprint, render_template, request, redirect, flash, url_for
from flask_login import login_required, current_user
from extensions import db
from models import Announcement, ActivityLog

announcement_bp = Blueprint("announcements", __name__, url_prefix="/pengumuman")


def log(user_id, tindakan, deskripsi):
    db.session.add(ActivityLog(user_id=user_id, tindakan=tindakan, deskripsi=deskripsi, model="Announcement"))
    db.session.commit()


@announcement_bp.route("/")
@login_required
def index():
    if current_user.role in ("admin", "management"):
        anns = Announcement.query.order_by(Announcement.created_at.desc()).all()
    else:
        anns = Announcement.query.filter_by(ditampilkan=True).order_by(Announcement.created_at.desc()).all()
    return render_template("announcements/index.html", announcements=anns)


@announcement_bp.route("/tambah", methods=["GET", "POST"])
@login_required
def create():
    if current_user.role not in ("admin", "management"):
        flash("Akses ditolak.", "danger")
        return redirect(url_for("announcements.index"))
    if request.method == "POST":
        a = Announcement(
            judul=request.form["judul"], isi=request.form["isi"],
            prioritas=request.form.get("prioritas", "normal"),
            ditampilkan=request.form.get("ditampilkan") == "on",
            created_by=current_user.id
        )
        db.session.add(a)
        log(current_user.id, "Buat pengumuman", f"Judul: {request.form['judul']}")
        db.session.commit()
        flash("Pengumuman berhasil dibuat.", "success")
        return redirect(url_for("announcements.index"))
    return render_template("announcements/form.html")


@announcement_bp.route("/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit(id):
    if current_user.role not in ("admin", "management"):
        flash("Akses ditolak.", "danger")
        return redirect(url_for("announcements.index"))
    a = Announcement.query.get_or_404(id)
    if request.method == "POST":
        a.judul = request.form["judul"]
        a.isi = request.form["isi"]
        a.prioritas = request.form.get("prioritas", "normal")
        a.ditampilkan = request.form.get("ditampilkan") == "on"
        log(current_user.id, "Edit pengumuman", f"Judul: {a.judul}")
        db.session.commit()
        flash("Pengumuman diperbarui.", "success")
        return redirect(url_for("announcements.index"))
    return render_template("announcements/form.html", announcement=a)


@announcement_bp.route("/hapus/<int:id>")
@login_required
def delete(id):
    if current_user.role not in ("admin", "management"):
        flash("Akses ditolak.", "danger")
        return redirect(url_for("announcements.index"))
    a = Announcement.query.get_or_404(id)
    log(current_user.id, "Hapus pengumuman", f"Judul: {a.judul}")
    db.session.delete(a)
    db.session.commit()
    flash("Pengumuman dihapus.", "success")
    return redirect(url_for("announcements.index"))
