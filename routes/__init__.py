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


def register_routes(app):
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
