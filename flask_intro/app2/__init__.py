from flask import Flask

def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.secret_key = "sdjfh834hf8h3f8h3f8h3f8h3f"

    from app2.views.general import general_bp
    from app2.views.menu import menu_bp
    from app2.views.reservation import reservations_bp
    from app2.views.admin import admin_bp

    app.register_blueprint(general_bp)
    app.register_blueprint(menu_bp)
    app.register_blueprint(reservations_bp)
    app.register_blueprint(admin_bp)

    return app
