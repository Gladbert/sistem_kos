from .auth import auth_bp
from .dashboard import dashboard_bp
from .rooms import rooms_bp
from .clients import clients_bp
from .payments import payments_bp
from .accounting import accounting_bp
from .maintenance import maintenance_bp
from .onboarding import onboarding_bp
from .announcements import announcement_bp
from .complaints import complaint_bp
from .activity_log import activity_bp
from .inventory import inventory_bp
from .audit import audit_bp
from .kos import kos_bp
from .fasilitas import fasilitas_bp
from .roles import roles_bp

def register_routes(app):
    app.register_blueprint(roles_bp)
    app.register_blueprint(kos_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(rooms_bp)
    app.register_blueprint(clients_bp)
    app.register_blueprint(payments_bp)
    app.register_blueprint(accounting_bp)
    app.register_blueprint(maintenance_bp)
    app.register_blueprint(onboarding_bp)
    app.register_blueprint(announcement_bp)
    app.register_blueprint(complaint_bp)
    app.register_blueprint(activity_bp)
    app.register_blueprint(inventory_bp)
    app.register_blueprint(audit_bp)
    app.register_blueprint(fasilitas_bp)

    # URL aliases for common guesses (ISSUE-015)
    from flask import redirect, url_for
    @app.route("/inventory/")
    def _inventory_alias():
        return redirect(url_for("inventory.index"))
    @app.route("/complaints/")
    def _complaints_alias():
        return redirect(url_for("complaint.index"))
    @app.route("/logs/")
    def _logs_alias():
        return redirect(url_for("activity.index"))
