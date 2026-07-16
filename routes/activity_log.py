from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_required, current_user
from models import ActivityLog

activity_bp = Blueprint("activity", __name__, url_prefix="/aktivitas")


@activity_bp.route("/")
@login_required
def index():
    if current_user.role not in ("admin", "management"):
        return redirect(url_for("dashboard.index"))
    model = request.args.get("model", "")
    tindakan = request.args.get("tindakan", "")
    q = ActivityLog.query
    if model:
        q = q.filter_by(model=model)
    if tindakan:
        q = q.filter(ActivityLog.tindakan.ilike(f"%{tindakan}%"))
    logs = q.order_by(ActivityLog.created_at.desc()).limit(200).all()
    models = [m[0] for m in ActivityLog.query.with_entities(ActivityLog.model).distinct().all()]
    return render_template("activity/index.html", logs=logs, models=models)
