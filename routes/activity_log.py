from flask import Blueprint, render_template, request, redirect, url_for, current_app
from flask_login import login_required, current_user
from models import ActivityLog

activity_bp = Blueprint("activity", __name__, url_prefix="/aktivitas")


@activity_bp.route("/")
@login_required
def index():
    if current_user.role not in ("admin", "management"):
        return redirect(url_for("dashboard.index"))
    page = request.args.get("page", 1, type=int)
    per_page = 50
    model = request.args.get("model", "")
    tindakan = request.args.get("tindakan", "")
    q = ActivityLog.query
    if model:
        q = q.filter_by(model=model)
    if tindakan:
        q = q.filter(ActivityLog.tindakan.ilike(f"%{tindakan}%"))
    pagination = q.order_by(ActivityLog.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    models = [m[0] for m in ActivityLog.query.with_entities(ActivityLog.model).distinct().all()]
    return render_template("activity/index.html", pagination=pagination, logs=pagination.items, models=models)
