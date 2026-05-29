from flask import Flask
from flask_socketio import SocketIO
from flask_mailman import Mail
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from datetime import timedelta

from app2.database import db, get_db
from app2.config import get_config

socketio   = SocketIO()
mail       = Mail()
login_manager = LoginManager()
csrf       = CSRFProtect()


def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")

    # Load config from config.py based on flask_env
    config = get_config()
    app.config.from_object(config)
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=8)
    app.config['SESSION_PERMANENT'] = True

    # ── Initialise extensions ──
    db.init_app(app)
    mail.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "customer_auth.login"
    csrf.init_app(app)
    socketio.init_app(app, cors_allowed_origins="*")

    # User loader for Flask-Login
    from app2.models.customer_user import CustomerUser

    @login_manager.user_loader
    def load_user(user_id):
        return CustomerUser.get_by_id(user_id)

    # Context processors
    @app.context_processor
    def inject_site_globals():
        """Injects hours, social links, branding, reviews, dishes into every template."""
        from app2.models.homepage_model import get_branding, get_reviews, get_dishes

        db_conn = get_db()
        cursor  = db_conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT * FROM restaurant_info 
            ORDER BY FIELD(day_of_week,
            'Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday')
        """)
        hours = cursor.fetchall()
        address = hours[0].get('address') if hours and hours[0].get('address') else None

        cursor.execute("""
            SELECT * FROM social_links 
            WHERE is_active = TRUE 
            ORDER BY display_order ASC
        """)
        social_links = cursor.fetchall()
        cursor.close()
        db_conn.close()

        return dict(
            restaurant_hours=hours,
            social_links=social_links,
            restaurant_address=address,
            branding=get_branding(),
            reviews=get_reviews(),
            dishes=get_dishes()
        )

    @app.context_processor
    def inject_theme():
        """Injects theme CSS vars into every template."""
        from app2.models.themeSettings_model import get_theme
        try:
            theme = get_theme()
        except Exception:
            theme = {
                'color_primary':    '#8B0000',
                'color_accent':     '#D4AF37',
                'color_background': '#F7F4EE',
                'color_surface':    '#FFFFFF',
                'color_text':       '#2C2416',
                'color_text_muted': '#9E8C78',
                'color_sidebar_bg': '#2C2416',
                'color_sidebar_text':'#FFFEF2',
                'font_body':        'Lato',
                'font_heading':     'Playfair Display',
                'border_radius':    '2px',
                'dark_mode':        False,
            }
        return dict(theme=theme)

    # Register blueprints
    from app2.views.general       import general_bp
    from app2.views.menu          import menu_bp
    from app2.views.reservation   import reservations_bp
    from app2.views.admin         import admin_bp
    from app2.views.cart          import cart_bp
    from app2.views.checkout      import checkout_bp
    from app2.views.customer_auth import customer_auth_bp
    from app2.views.orders        import orders_bp
    from app2.views.staff         import staff_bp
    from app2.views.guest_lookup  import guest_lookup_bp

    app.register_blueprint(general_bp)
    app.register_blueprint(menu_bp)
    app.register_blueprint(reservations_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(cart_bp)
    app.register_blueprint(checkout_bp)
    app.register_blueprint(customer_auth_bp)
    app.register_blueprint(orders_bp)
    app.register_blueprint(staff_bp)
    app.register_blueprint(guest_lookup_bp)

    # SocketIO event handlers

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

    @socketio.on('join_kitchen')
    def join_kitchen():
        from flask_socketio import join_room
        join_room('kitchen')

    @socketio.on("join_order")
    def join_order(data):
        from flask_socketio import join_room
        order_id = data.get("order_id")
        if order_id:
            join_room(f"order_{order_id}")

    @socketio.on("driver_response")
    def driver_response(data):
        """
        Handles driver accept/decline.
        Updates customer_orders, emits result back to admin room.
        Moved SQL to Order model method.
        """
        from flask_socketio import emit
        from app2.models.order_model import Order

        order_id = data["order_id"]
        accepted = data["accepted"]

        order = Order.get_by_id(order_id)
        if not order:
            return

        # Guard — ignore if already responded
        if order.driver_offer_status in ("accepted", "declined"):
            return

        if accepted:
            Order.accept_driver_offer(order_id)
        else:
            Order.decline_driver_offer(order_id)

        emit("driver_response_update", {
            "order_id": order_id,
            "accepted": accepted
        }, room="admin_room")

    @socketio.on('driver_location_update')
    def handle_driver_location(data):
        from flask_socketio import emit
        order_id = data.get('order_id')
        lat      = data.get('lat')
        lng      = data.get('lng')
        if order_id and lat and lng:
            emit('driver_moved', {'lat': lat, 'lng': lng}, room=f'order_{order_id}')

    return app