import urllib.parse
from functools import wraps
from flask import flash, redirect, url_for, session, abort
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


def get_current_kos_role():
    """Return user's role for current session kos, or None."""
    from models import UserKos
    kos_id = session.get("kos_id")
    if not kos_id:
        return None
    if current_user.role == "admin":
        return "admin"
    uk = UserKos.query.filter_by(user_id=current_user.id, kos_id=kos_id).first()
    return uk.role if uk else None


def require_kos_role(*roles):
    """Decorator: require login + specific role(s) for current session kos.
    Falls back to global role check for backward compatibility.
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for("auth.login"))
            
            kos_role = get_current_kos_role()
            
            # Fallback: check global role if no UserKos entry exists
            if kos_role is None:
                if current_user.role in roles:
                    return f(*args, **kwargs)
                flash("Akses ditolak.", "danger")
                return redirect(url_for("dashboard.index"))
            
            if kos_role not in roles:
                flash("Akses ditolak.", "danger")
                return redirect(url_for("dashboard.index"))
            
            return f(*args, **kwargs)
        return decorated
    return decorator


# Backward-compatible decorator
def admin_or_management(f):
    """Decorator: require login + admin/management role (per-kos or global)."""
    return require_kos_role("admin", "management")(f)


def get_or_404(model, id):
    """Get model by primary key or abort(404)."""
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
