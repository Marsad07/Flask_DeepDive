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
        return dict(
            restaurant_hours=hours,
            restaurant_address=address,
            branding=branding,
            reviews=reviews,
            dishes=dishes
        )

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

    @socketio.on("join_admin")
    def join_admin():
        from flask_socketio import join_room
        join_room("admin_room")

    @socketio.on("join_driver")
    def join_driver(data):
        from flask_socketio import join_room
        driver_id = data.get("driver_id")
        if driver_id:
            join_room(f"driver_{driver_id}")

    @socketio.on("join_order")
    def join_order(data):
        from flask_socketio import join_room
        order_id = data.get("order_id")
        if order_id:
            join_room(f"order_{order_id}")

    socketio.on("driver_response")

    @socketio.on("driver_response")
    def driver_response(data):
        from flask_socketio import emit
        order_id = data["order_id"]
        accepted = data["accepted"]

        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            SELECT driver_offer_status
            FROM customer_orders
            WHERE order_id = %s
        """, (order_id,))
        existing = cursor.fetchone()

        if existing["driver_offer_status"] in ("accepted", "declined"):
            return  # ignore duplicates

        if accepted:
            cursor.execute("""
                UPDATE customer_orders
                SET assigned_driver_id = driver_offer_id,
                    driver_offer_status = 'accepted'
                WHERE order_id = %s
            """, (order_id,))
        else:
            cursor.execute("""
                UPDATE customer_orders
                SET driver_offer_id = NULL,
                    driver_offer_status = 'declined',
                    order_status = 'pending'
                WHERE order_id = %s
            """, (order_id,))

        db.commit()
        cursor.close()
        db.close()
        emit("driver_response_update", {
            "order_id": order_id,
            "accepted": accepted
        }, room="admin_room")

    return app