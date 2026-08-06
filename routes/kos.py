from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_required, current_user
from extensions import db
from models import Kos
from helpers import log_activity

kos_bp = Blueprint("kos", __name__, url_prefix="/kos")


@kos_bp.route("/pilih/<int:id>", methods=["POST"])
@login_required
def pilih(id):
    kos = Kos.query.get_or_404(id)
    session["kos_id"] = kos.id
    flash(f"Beralih ke {kos.nama}.", "success")
    return redirect(request.referrer or url_for("dashboard.admin"))


@kos_bp.route("/")
@login_required
def index():
    if current_user.role not in ("admin", "management"):
        flash("Akses ditolak.", "danger")
        return redirect(url_for("dashboard.index"))
    semua_kos = Kos.query.order_by(Kos.nama).all()
    return render_template("kos/index.html", semua_kos=semua_kos)


@kos_bp.route("/tambah", methods=["GET", "POST"])
@login_required
def tambah():
    if current_user.role not in ("admin", "management"):
        flash("Akses ditolak.", "danger")
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        nama = request.form.get("nama", "").strip()
        if not nama:
            flash("Nama kos wajib diisi.", "danger")
            return render_template("kos/form.html", kos=None)

        kos = Kos(
            nama=nama,
            alamat=request.form.get("alamat", "").strip(),
            deskripsi=request.form.get("deskripsi", "").strip(),
        )
        db.session.add(kos)
        db.session.commit()
        log_activity(current_user.id, "Tambah kos", f"Nama: {nama}", "Kos")
        flash(f"Kos \"{nama}\" berhasil ditambahkan.", "success")
        return redirect(url_for("kos.index"))

    return render_template("kos/form.html", kos=None)


@kos_bp.route("/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit(id):
    if current_user.role not in ("admin", "management"):
        flash("Akses ditolak.", "danger")
        return redirect(url_for("dashboard.index"))

    kos = Kos.query.get_or_404(id)

    if request.method == "POST":
        nama = request.form.get("nama", "").strip()
        if not nama:
            flash("Nama kos wajib diisi.", "danger")
            return render_template("kos/form.html", kos=kos)

        kos.nama = nama
        kos.alamat = request.form.get("alamat", "").strip()
        kos.deskripsi = request.form.get("deskripsi", "").strip()
        db.session.commit()
        log_activity(current_user.id, "Edit kos", f"Nama: {nama}", "Kos")
        flash(f"Kos \"{nama}\" berhasil diperbarui.", "success")
        return redirect(url_for("kos.index"))

    return render_template("kos/form.html", kos=kos)


@kos_bp.route("/hapus/<int:id>", methods=["POST"])
@login_required
def hapus(id):
    if current_user.role not in ("admin",):
        flash("Hanya admin yang bisa menghapus kos.", "danger")
        return redirect(url_for("kos.index"))

    kos = Kos.query.get_or_404(id)
    if kos.rooms.count() > 0:
        flash(f"Tidak bisa hapus \"{kos.nama}\" — masih ada {kos.rooms.count()} kamar.", "danger")
        return redirect(url_for("kos.index"))

    nama = kos.nama
    db.session.delete(kos)
    db.session.commit()
    flash(f"Kos \"{nama}\" berhasil dihapus.", "success")
    return redirect(url_for("kos.index"))
