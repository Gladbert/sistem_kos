from extensions import db
from models import ActivityLog


def log_activity(user_id, tindakan, deskripsi="", model=""):
    db.session.add(ActivityLog(user_id=user_id, tindakan=tindakan, deskripsi=deskripsi, model=model))
    db.session.commit()
