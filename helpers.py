import urllib.parse
from functools import wraps
from flask import flash, redirect, url_for, session
from flask_login import current_user
from extensions import db


def parse_amount(raw, label="Jumlah"):
    """Parse form value to float > 0. Returns (value, error_msg)."""
    try:
        val = float(raw or 0)
    except (ValueError, TypeError):
        return None, f"{label} harus angka."
    if val <= 0:
        return None, f"{label} harus lebih dari 0."
    return val, None


def create_notification(user_id, pesan, jenis="umum", wa_sent=False):
    """Add + commit a Notification in one call."""
    from models import Notification
    db.session.add(Notification(user_id=user_id, pesan=pesan, jenis=jenis, wa_sent=wa_sent))
    db.session.commit()


def wa_redirect(phone, message):
    """Build WhatsApp redirect response."""
    return redirect(f"https://wa.me/{phone}?text={urllib.parse.quote(message)}")


def kos_expense_query(base_query):
    """Apply kos_id filter to an Expense query if session kos is set."""
    from models import Expense
    kos_id = session.get("kos_id")
    if kos_id:
        return base_query.filter(Expense.kos_id == kos_id)
    return base_query


def log_activity(user_id, tindakan, deskripsi="", model=""):
    from models import ActivityLog
    db.session.add(ActivityLog(user_id=user_id, tindakan=tindakan, deskripsi=deskripsi, model=model))
    db.session.commit()

def admin_or_management(f):
    """Decorator: require login + admin/management role."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for("auth.login"))
        if current_user.role not in ("admin", "management"):
            flash("Akses ditolak.", "danger")
            return redirect(url_for("dashboard.index"))
        return f(*args, **kwargs)
    return decorated

def get_or_404(model, id):
    """Get model by primary key or abort(404). Replaces deprecated Model.query.get_or_404()."""
    from flask import abort
    obj = db.session.get(model, id)
    if obj is None:
        abort(404)
    return obj

def kos_room_ids(kos_id=None):
    """Return list of room IDs for the given kos (or session kos). Empty list if none."""
    from models import Room
    if kos_id is None:
        kos_id = session.get("kos_id")
    if not kos_id:
        return []
    return [r.id for r in db.session.query(Room.id).filter_by(kos_id=kos_id).all()]

def kos_rooms(kos_id=None):
    """Return Room objects for the given kos (or session kos). All rooms if none."""
    from models import Room
    if kos_id is None:
        kos_id = session.get("kos_id")
    if kos_id:
        return Room.query.filter_by(kos_id=kos_id).all()
    return Room.query.all()

def safe_commit():
    """Commit with rollback on error. Returns True on success."""
    from flask import current_app
    try:
        db.session.commit()
        return True
    except Exception:
        current_app.logger.exception("Database commit failed")
        db.session.rollback()
        raise
