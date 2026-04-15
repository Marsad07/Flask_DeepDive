from flask import Flask
from app2.database import get_db
from flask_socketio import SocketIO
from flask_mailman import Mail
import os
from app2.models.homepage_model import get_branding, get_reviews, get_dishes

socketio = SocketIO()
mail = Mail()

def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")

    app.secret_key = os.getenv("sdjfh834hf8h3f8h3f8h3f8h3f", "dev-secret-key")

    socketio.init_app(app)

    app.config["MAIL_SERVER"] = "smtp.gmail.com"
    app.config["MAIL_PORT"] = 587
    app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")
    app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")
    app.config["MAIL_USE_TLS"] = True
    app.config["MAIL_USE_SSL"] = False
    mail.init_app(app)

    @app.context_processor
    def inject_hrs():
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            SELECT * FROM restaurant_info 
            ORDER BY FIELD(day_of_week,
            'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday')
        """)
        hours = cursor.fetchall()

        address = None
        if hours and hours[0].get('address'):
            address = hours[0].get('address')

        branding = get_branding()
        reviews = get_reviews()
        dishes = get_dishes()

        cursor.close()
        db.close()
        return dict(restaurant_hours=hours, restaurant_address=address, branding=branding, reviews=reviews,
                    dishes=dishes)

    from app2.views.general import general_bp
    from app2.views.menu import menu_bp
    from app2.views.reservation import reservations_bp
    from app2.views.admin import admin_bp
    from app2.views.cart import cart_bp
    from app2.views.checkout import checkout_bp
    from app2.views.customer_auth import customer_auth_bp
    from app2.views.orders import orders_bp
    from app2.views.staff import staff_bp

    app.register_blueprint(general_bp)
    app.register_blueprint(menu_bp)
    app.register_blueprint(reservations_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(cart_bp)
    app.register_blueprint(checkout_bp)
    app.register_blueprint(customer_auth_bp)
    app.register_blueprint(orders_bp)
    app.register_blueprint(staff_bp)

    return app