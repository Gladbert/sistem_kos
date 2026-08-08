from flask import Blueprint, render_template, redirect, url_for, flash, request, session, current_app
from flask_login import login_required, current_user
from extensions import db
from models import FasilitasUmum, FasilitasKategori
from helpers import admin_or_management, get_or_404, safe_commit, log_activity, sanitize

fasilitas_bp = Blueprint("fasilitas", __name__, url_prefix="/fasilitas")

KONDISI = ["baik", "rusak_ringan", "rusak_berat", "maintenance"]
FREKUENSI = [
    ("bulanan", "Bulanan"),
    ("3_bulan", "3 Bulan"),
    ("6_bulan", "6 Bulan"),
    ("tahunan", "Tahunan"),
]

def get_kategori_list():
    return FasilitasKategori.query.filter_by(is_active=True).order_by(FasilitasKategori.nama).all()

# ── FASILITAS UMUM ──

@fasilitas_bp.route("/")
@admin_or_management
def index():
    kos_id = session.get("kos_id")
    q = FasilitasUmum.query
    if kos_id:
        q = q.filter_by(kos_id=kos_id)
    
    kategori_filter = request.args.get("kategori")
    if kategori_filter:
        q = q.filter_by(kategori=kategori_filter)
    
    items = q.order_by(FasilitasUmum.kategori, FasilitasUmum.nama).all()
    
    total = len(items)
    baik = sum(1 for i in items if i.kondisi == "baik")
    rusak = sum(1 for i in items if i.kondisi.startswith("rusak"))
    maint = sum(1 for i in items if i.kondisi == "maintenance")
    
    return render_template("fasilitas/index.html",
        items=items, kategori_list=get_kategori_list(), kondisi_list=KONDISI,
        kategori_filter=kategori_filter,
        total=total, baik=baik, rusak=rusak, maintenance=maint)

@fasilitas_bp.route("/tambah", methods=["GET", "POST"])
@admin_or_management
def tambah():
    if request.method == "POST":
        nama = request.form.get("nama", "").strip()
        if not nama:
            flash("Nama fasilitas wajib diisi.", "danger")
            return render_template("fasilitas/form.html", kategori_list=get_kategori_list(), kondisi_list=KONDISI, frekuensi_list=FREKUENSI, item=None)

        item = FasilitasUmum(
            kos_id=session.get("kos_id"),
            nama=sanitize(nama),
            kategori=request.form.get("kategori", "lainnya"),
            lokasi=sanitize(request.form.get("lokasi")),
            kondisi=request.form.get("kondisi", "baik"),
            deskripsi=sanitize(request.form.get("deskripsi")),
            catatan=sanitize(request.form.get("catatan")),
            is_recurring=request.form.get("is_recurring") == "1",
            biaya_per_bulan=float(request.form.get("biaya_per_bulan") or 0) if request.form.get("biaya_per_bulan") else None,
            frekuensi=request.form.get("frekuensi", "bulanan"),
        )
        db.session.add(item)
        try:
            safe_commit()
        except Exception:
            current_app.logger.exception("Failed to add fasilitas")
            db.session.rollback()
            flash("Gagal menyimpan data.", "danger")
            return redirect(request.referrer or url_for("fasilitas.index"))
        log_activity(current_user.id, "Tambah fasilitas umum", f"{item.nama} ({item.kategori})", "FasilitasUmum")
        flash(f"Fasilitas '{item.nama}' berhasil ditambahkan.", "success")
        return redirect(url_for("fasilitas.index"))
    
    return render_template("fasilitas/form.html", kategori_list=get_kategori_list(), kondisi_list=KONDISI, frekuensi_list=FREKUENSI, item=None)

@fasilitas_bp.route("/edit/<int:id>", methods=["GET", "POST"])
@admin_or_management
def edit(id):
    item = get_or_404(FasilitasUmum, id)
    
    if request.method == "POST":
        nama = request.form.get("nama", "").strip()
        if not nama:
            flash("Nama fasilitas wajib diisi.", "danger")
            return render_template("fasilitas/form.html", kategori_list=get_kategori_list(), kondisi_list=KONDISI, frekuensi_list=FREKUENSI, item=item)

        old_kondisi = item.kondisi
        item.nama = sanitize(nama)
        item.kategori = request.form.get("kategori", "lainnya")
        item.lokasi = sanitize(request.form.get("lokasi"))
        item.kondisi = request.form.get("kondisi", "baik")
        item.deskripsi = sanitize(request.form.get("deskripsi"))
        item.catatan = sanitize(request.form.get("catatan"))
        item.is_recurring = request.form.get("is_recurring") == "1"
        item.biaya_per_bulan = float(request.form.get("biaya_per_bulan") or 0) if request.form.get("biaya_per_bulan") else None
        item.frekuensi = request.form.get("frekuensi", "bulanan")
        
        try:
            safe_commit()
        except Exception:
            current_app.logger.exception("Failed to update fasilitas")
            db.session.rollback()
            flash("Gagal menyimpan data.", "danger")
            return redirect(request.referrer or url_for("fasilitas.index"))
        
        if old_kondisi == "baik" and item.kondisi.startswith("rusak"):
            flash(f"'{item.nama}' ditandai rusak. Tambahkan pengeluaran jika ada biaya perbaikan.", "warning")
        else:
            flash(f"Fasilitas '{item.nama}' berhasil diperbarui.", "success")
        return redirect(url_for("fasilitas.index"))
    
    return render_template("fasilitas/form.html", kategori_list=get_kategori_list(), kondisi_list=KONDISI, frekuensi_list=FREKUENSI, item=item)

@fasilitas_bp.route("/hapus/<int:id>", methods=["POST"])
@admin_or_management
def hapus(id):
    item = get_or_404(FasilitasUmum, id)
    nama = item.nama
    db.session.delete(item)
    try:
        safe_commit()
    except Exception:
        current_app.logger.exception("Failed to delete fasilitas")
        db.session.rollback()
        flash("Gagal menghapus data.", "danger")
        return redirect(request.referrer or url_for("fasilitas.index"))
    log_activity(current_user.id, "Hapus fasilitas umum", nama, "FasilitasUmum")
    flash(f"Fasilitas '{nama}' berhasil dihapus.", "success")
    return redirect(url_for("fasilitas.index"))

@fasilitas_bp.route("/<int:id>/laporkan-rusak", methods=["POST"])
@admin_or_management
def laporkan_rusak(id):
    item = get_or_404(FasilitasUmum, id)
    item.kondisi = "rusak_berat"
    try:
        safe_commit()
    except Exception:
        current_app.logger.exception("Failed to update fasilitas kondisi")
        db.session.rollback()
        flash("Gagal menyimpan data.", "danger")
        return redirect(request.referrer or url_for("fasilitas.index"))
    log_activity(current_user.id, "Laporkan rusak", item.nama, "FasilitasUmum")
    flash(f"'{item.nama}' ditandai rusak. Tambahkan pengeluaran untuk biaya perbaikan.", "warning")
    return redirect(url_for("accounting.tambah_pengeluaran"))

# ── KATEGORI MANAGEMENT ──

@fasilitas_bp.route("/kategori")
@admin_or_management
def kategori_index():
    items = FasilitasKategori.query.order_by(FasilitasKategori.nama).all()
    return render_template("fasilitas/kategori.html", items=items)

@fasilitas_bp.route("/kategori/tambah", methods=["GET", "POST"])
@admin_or_management
def kategori_tambah():
    if request.method == "POST":
        raw_nama = request.form.get("nama", "").strip()
        if not raw_nama:
            flash("Nama kategori wajib diisi.", "danger")
            return render_template("fasilitas/kategori_form.html", item=None)

        nama = raw_nama.lower().replace(" ", "_")
        if FasilitasKategori.query.filter_by(nama=nama).first():
            flash(f"Kategori '{nama}' sudah ada.", "warning")
            return redirect(url_for("fasilitas.kategori_index"))
        
        kat = FasilitasKategori(
            nama=nama,
            icon=request.form.get("icon", "bi-box"),
            deskripsi=sanitize(request.form.get("deskripsi")),
        )
        db.session.add(kat)
        try:
            safe_commit()
        except Exception:
            current_app.logger.exception("Failed to add kategori")
            db.session.rollback()
            flash("Gagal menyimpan data.", "danger")
            return redirect(request.referrer or url_for("fasilitas.kategori_index"))
        flash(f"Kategori '{nama}' berhasil ditambahkan.", "success")
        return redirect(url_for("fasilitas.kategori_index"))
    
    return render_template("fasilitas/kategori_form.html", item=None)

@fasilitas_bp.route("/kategori/edit/<int:id>", methods=["GET", "POST"])
@admin_or_management
def kategori_edit(id):
    item = get_or_404(FasilitasKategori, id)
    
    if request.method == "POST":
        raw_nama = request.form.get("nama", "").strip()
        if not raw_nama:
            flash("Nama kategori wajib diisi.", "danger")
            return render_template("fasilitas/kategori_form.html", item=item)

        item.nama = raw_nama.lower().replace(" ", "_")
        item.icon = request.form.get("icon", "bi-box")
        item.deskripsi = sanitize(request.form.get("deskripsi"))
        item.is_active = "is_active" in request.form
        try:
            safe_commit()
        except Exception:
            current_app.logger.exception("Failed to update kategori")
            db.session.rollback()
            flash("Gagal menyimpan data.", "danger")
            return redirect(request.referrer or url_for("fasilitas.kategori_index"))
        flash(f"Kategori '{item.nama}' berhasil diperbarui.", "success")
        return redirect(url_for("fasilitas.kategori_index"))
    
    return render_template("fasilitas/kategori_form.html", item=item)

@fasilitas_bp.route("/kategori/hapus/<int:id>", methods=["POST"])
@admin_or_management
def kategori_hapus(id):
    item = get_or_404(FasilitasKategori, id)
    count = FasilitasUmum.query.filter_by(kategori=item.nama).count()
    if count > 0:
        flash(f"Tidak bisa hapus '{item.nama}' karena masih digunakan oleh {count} fasilitas.", "danger")
        return redirect(url_for("fasilitas.kategori_index"))
    
    nama = item.nama
    db.session.delete(item)
    try:
        safe_commit()
    except Exception:
        current_app.logger.exception("Failed to delete kategori")
        db.session.rollback()
        flash("Gagal menghapus data.", "danger")
        return redirect(request.referrer or url_for("fasilitas.kategori_index"))
    flash(f"Kategori '{nama}' berhasil dihapus.", "success")
    return redirect(url_for("fasilitas.kategori_index"))
