from flask import Blueprint, render_template, redirect, url_for, flash, request, session, current_app
from flask_login import login_required, current_user
from extensions import db
from models import Kos, UserKos
from helpers import log_activity, admin_or_management, get_or_404, safe_commit, sanitize

kos_bp = Blueprint("kos", __name__, url_prefix="/kos")

@kos_bp.route("/pilih/<int:id>", methods=["POST"])
@login_required
def pilih(id):
    kos = get_or_404(Kos, id)
    if not kos.is_active:
        flash("Kos tidak aktif.", "danger")
        return redirect(request.referrer or url_for("dashboard.admin"))
    
    # Verify user has access to this kos
    if not current_user.has_kos_access(id):
        flash("Anda tidak memiliki akses ke kos ini.", "danger")
        return redirect(request.referrer or url_for("dashboard.index"))
    
    session["kos_id"] = kos.id
    flash(f"Beralih ke {kos.nama}.", "success")
    return redirect(request.referrer or url_for("dashboard.admin"))

@kos_bp.route("/")
@admin_or_management
def index():
    # Only show kos the user has access to
    if current_user.role == "admin":
        semua_kos = Kos.query.order_by(Kos.nama).all()
    else:
        kos_ids = current_user.get_accessible_kos_ids()
        semua_kos = Kos.query.filter(Kos.id.in_(kos_ids)).order_by(Kos.nama).all() if kos_ids else []
    return render_template("kos/index.html", semua_kos=semua_kos)

@kos_bp.route("/tambah", methods=["GET", "POST"])
@admin_or_management
def tambah():
    if request.method == "POST":
        nama = request.form.get("nama", "").strip()
        submitted = {
            "nama": nama,
            "alamat": request.form.get("alamat", ""),
            "deskripsi": request.form.get("deskripsi", ""),
        }
        if not nama:
            flash("Nama kos wajib diisi.", "danger")
            return render_template("kos/form.html", kos=None, submitted=submitted)

        kos = Kos(
            nama=sanitize(nama),
            alamat=sanitize(request.form.get("alamat", "")),
            deskripsi=sanitize(request.form.get("deskripsi", "")),
        )
        db.session.add(kos)
        try:
            safe_commit()
        except Exception:
            current_app.logger.exception("Database operation failed")
            db.session.rollback()
            flash("Terjadi kesalahan saat menyimpan data.", "danger")
            return redirect(request.referrer or url_for("dashboard.index"))
        
        # Auto-assign creator as admin of this kos
        user_kos = UserKos(user_id=current_user.id, kos_id=kos.id, role="admin")
        db.session.add(user_kos)
        db.session.commit()
        
        log_activity(current_user.id, "Tambah kos", f"Nama: {nama}", "Kos")
        flash(f'Kos "{nama}" berhasil ditambahkan.', "success")
        return redirect(url_for("kos.index"))

    return render_template("kos/form.html", kos=None)

@kos_bp.route("/edit/<int:id>", methods=["GET", "POST"])
@admin_or_management
def edit(id):
    kos = get_or_404(Kos, id)
    
    # Verify access
    if not current_user.has_kos_access(id, ["admin", "management"]):
        flash("Akses ditolak.", "danger")
        return redirect(url_for("kos.index"))

    if request.method == "POST":
        nama = request.form.get("nama", "").strip()
        if not nama:
            flash("Nama kos wajib diisi.", "danger")
            return render_template("kos/form.html", kos=kos)

        kos.nama = sanitize(nama)
        kos.alamat = sanitize(request.form.get("alamat", ""))
        kos.deskripsi = sanitize(request.form.get("deskripsi", ""))
        try:
            safe_commit()
        except Exception:
            current_app.logger.exception("Database operation failed")
            db.session.rollback()
            flash("Terjadi kesalahan saat menyimpan data.", "danger")
            return redirect(request.referrer or url_for("dashboard.index"))
        log_activity(current_user.id, "Edit kos", f"Nama: {nama}", "Kos")
        flash(f'Kos "{nama}" berhasil diperbarui.', "success")
        return redirect(url_for("kos.index"))

    return render_template("kos/form.html", kos=kos)

@kos_bp.route("/hapus/<int:id>", methods=["POST"])
@login_required
def hapus(id):
    # Only kos admin can delete
    kos_role = current_user.get_role_for_kos(id)
    if kos_role != "admin" and current_user.role != "admin":
        flash("Hanya admin kos yang bisa menghapus.", "danger")
        return redirect(url_for("kos.index"))

    kos = get_or_404(Kos, id)
    if kos.rooms.count() > 0:
        flash(f'Tidak bisa hapus "{kos.nama}" — masih ada {kos.rooms.count()} kamar.', "danger")
        return redirect(url_for("kos.index"))

    nama = kos.nama
    db.session.delete(kos)
    try:
        safe_commit()
    except Exception:
        current_app.logger.exception("Database operation failed")
        db.session.rollback()
        flash("Terjadi kesalahan saat menyimpan data.", "danger")
        return redirect(request.referrer or url_for("dashboard.index"))
    flash(f'Kos "{nama}" berhasil dihapus.', "success")
    return redirect(url_for("kos.index"))

@kos_bp.route("/unduran", methods=["GET", "POST"])
@login_required
def unduran():
    """Manage invite codes for current kos."""
    kos_id = session.get("kos_id")
    if not kos_id:
        flash("Pilih kos terlebih dahulu.", "warning")
        return redirect(url_for("kos.index"))
    
    kos_role = current_user.get_role_for_kos(kos_id)
    if kos_role not in ("admin", "management") and current_user.role != "admin":
        flash("Akses ditolak.", "danger")
        return redirect(url_for("dashboard.index"))
    
    from models import KosInvite
    
    if request.method == "POST":
        role = request.form.get("role", "client")
        if role not in ("admin", "management", "client"):
            role = "client"
        
        invite = KosInvite(
            kos_id=kos_id,
            code=KosInvite.generate_code(),
            role=role,
            created_by=current_user.id,
        )
        db.session.add(invite)
        db.session.commit()
        flash(f"Kode undangan dibuat: {invite.code} (role: {role})", "success")
        return redirect(url_for("kos.unduran"))
    
    invites = KosInvite.query.filter_by(kos_id=kos_id).order_by(KosInvite.created_at.desc()).all()
    return render_template("kos/unduran.html", invites=invites, kos=kos)
