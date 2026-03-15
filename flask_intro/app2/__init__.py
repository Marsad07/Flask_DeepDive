from flask import Flask

def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.secret_key = "sdjfh834hf8h3f8h3f8h3f8h3f"

    @app.context_processor
    def inject_hrs():
        from app2.database import  restaurant_db1
        cursor = restaurant_db1.cursor(dictionary=True)
        cursor.execute("""
                   SELECT * FROM restaurant_info 
                   ORDER BY FIELD(day_of_week,
                    'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday')
               """)
        hours = cursor.fetchall()
        return dict(restaurant_hours=hours)

    from app2.views.general import general_bp
    from app2.views.menu import menu_bp
    from app2.views.reservation import reservations_bp
    from app2.views.admin import admin_bp

    app.register_blueprint(general_bp)
    app.register_blueprint(menu_bp)
    app.register_blueprint(reservations_bp)
    app.register_blueprint(admin_bp)

    return app
