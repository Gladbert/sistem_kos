from flask import Flask, session
from extensions import db, login_manager, csrf, limiter


def create_app():
    app = Flask(__name__)
    app.config.from_object("config.Config")

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)

    login_manager.login_view = "auth.login"
    login_manager.login_message = "Silakan login terlebih dahulu."

    from models import User, Kos

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    @app.context_processor
    def inject_now():
        from datetime import datetime
        return {"now": datetime.now()}

    @app.context_processor
    def inject_utility():
        from datetime import date
        return {"date_today": date.today()}

    @app.context_processor
    def inject_kos():
        from flask_login import current_user
        if not current_user.is_authenticated:
            return {"all_kos": [], "current_kos": None}
        all_kos = Kos.query.filter_by(is_active=True).order_by(Kos.nama).all()
        kos_id = session.get("kos_id")
        current_kos = None
        if kos_id:
            current_kos = Kos.query.get(kos_id)
        if not current_kos and all_kos:
            current_kos = all_kos[0]
            session["kos_id"] = current_kos.id
        return {"all_kos": all_kos, "current_kos": current_kos}

    from routes import register_routes
    register_routes(app)

    with app.app_context():
        db.create_all()

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, host="0.0.0.0", port=5000)
