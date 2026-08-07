from flask import Flask, session, render_template, redirect, url_for
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
        return db.session.get(User, int(user_id))

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
        try:
            all_kos = Kos.query.filter_by(is_active=True).order_by(Kos.nama).all()
            kos_id = session.get("kos_id")
            current_kos = None
            if kos_id:
                current_kos = db.session.get(Kos, kos_id)
                if current_kos and not current_kos.is_active:
                    current_kos = None
                    session.pop("kos_id", None)
            if not current_kos and all_kos:
                current_kos = all_kos[0]
                session["kos_id"] = current_kos.id
            return {"all_kos": all_kos, "current_kos": current_kos}
        except Exception:
            return {"all_kos": [], "current_kos": None}

    from routes import register_routes
    register_routes(app)

    @app.route("/")
    def root():
        return redirect(url_for("dashboard.index"))

    @app.route("/finance")
    def finance_redirect():
        return redirect(url_for("accounting.index"))


    # Error handlers — use minimal templates to avoid DB queries
    @app.errorhandler(404)
    def not_found(e):
        return "<h1>404 — Halaman tidak ditemukan</h1><p><a href='/'>Kembali</a></p>", 404

    @app.errorhandler(500)
    def server_error(e):
        app.logger.exception("Internal server error")
        return "<h1>500 — Terjadi kesalahan</h1><p><a href='/'>Kembali</a></p>", 500

    @app.errorhandler(403)
    def forbidden(e):
        return "<h1>403 — Akses ditolak</h1><p><a href='/'>Kembali</a></p>", 403

    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
