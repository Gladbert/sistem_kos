from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from extensions import db
from models import RolePermission
from helpers import admin_only, safe_commit

roles_bp = Blueprint("roles", __name__, url_prefix="/admin/roles")

MODULES = [
    ("dashboard", "Dashboard", "bi-grid"),
    ("rooms", "Kamar", "bi-door-open"),
    ("clients", "Penghuni", "bi-people"),
    ("payments", "Pembayaran", "bi-credit-card"),
    ("accounting", "Keuangan", "bi-graph-up"),
    ("maintenance", "Maintenance", "bi-tools"),
    ("vendors", "Vendor", "bi-truck"),
    ("announcements", "Pengumuman", "bi-megaphone"),
    ("complaints", "Komplain", "bi-chat-dots"),
    ("inventory", "Inventaris", "bi-box-seam"),
    ("fasilitas", "Fasilitas", "bi-building"),
    ("kos", "Kelola Kos", "bi-buildings"),
    ("activity_log", "Log Aktivitas", "bi-clock-history"),
    ("audit", "Audit Kamar", "bi-clipboard-check"),
]


@roles_bp.route("/")
@admin_only
def index():
    roles = ["admin", "management", "client"]
    perms = {}
    for role in roles:
        perms[role] = {}
        for module_key, _, _ in MODULES:
            p = RolePermission.query.filter_by(role=role, module=module_key).first()
            if p:
                perms[role][module_key] = {
                    "view": p.can_view,
                    "create": p.can_create,
                    "edit": p.can_edit,
                    "delete": p.can_delete,
                }
            else:
                perms[role][module_key] = {
                    "view": False, "create": False, "edit": False, "delete": False,
                }
    return render_template("admin/roles.html", modules=MODULES, roles=roles, perms=perms)


@roles_bp.route("/update", methods=["POST"])
@admin_only
def update():
    roles = ["admin", "management", "client"]
    actions = ["view", "create", "edit", "delete"]

    for role in roles:
        if role == "admin":
            continue  # admin always full access
        for module_key, _, _ in MODULES:
            p = RolePermission.query.filter_by(role=role, module=module_key).first()
            if not p:
                p = RolePermission(role=role, module=module_key)
                db.session.add(p)

            for action in actions:
                field = f"{role}_{module_key}_{action}"
                val = field in request.form
                setattr(p, f"can_{action}", val)

    if safe_commit():
        flash("Hak akses berhasil diperbarui.", "success")
    else:
        flash("Gagal menyimpan perubahan.", "danger")

    return redirect(url_for("roles.index"))
