from flask import Blueprint
from app2.controllers.admin_controller import (admin_login, dashboard, logout, view_reservations, manage_menu,
                                               add_menu_item, edit_menu_item, delete_menu_item, update_hours,
                                               view_analytics, view_all_orders, view_customer_order)

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

admin_bp.route("/login", methods=["GET", "POST"])(admin_login)
admin_bp.route("/dashboard")(dashboard)
admin_bp.route("/logout")(logout)
admin_bp.route("/reservations")(view_reservations)
admin_bp.route("/menu")(manage_menu)
admin_bp.route("/menu/add", methods=["GET", "POST"])(add_menu_item)
admin_bp.route("/menu/edit/<int:item_id>", methods=["GET", "POST"])(edit_menu_item)
admin_bp.route("/menu/delete/<int:item_id>", methods=["POST"])(delete_menu_item)
admin_bp.route("/update_hours", methods=["GET", "POST"])(update_hours)
admin_bp.route("/analytics")(view_analytics)
admin_bp.route("/view_all_orders")(view_all_orders)
admin_bp.route("/customer_order/<int:order_id>")(view_customer_order)