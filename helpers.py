from functools import wraps
from flask import flash, redirect, url_for, session
from flask_login import current_user
from extensions import db


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
