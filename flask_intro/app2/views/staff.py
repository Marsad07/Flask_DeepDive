from flask import Blueprint
from app2.controllers.staff_controller import (staff_login, kitchen_display, staff_logout, kitchen_update_order_status,
                                               driver_orders, toggle_driver_availability, update_delivery_status)
staff_bp = Blueprint('staff', __name__, url_prefix='/staff')

staff_bp.route('/login', methods=['GET', 'POST'])(staff_login)
staff_bp.route('/kitchen')(kitchen_display)
staff_bp.route('/logout')(staff_logout)
staff_bp.route('/kitchen/order/<int:order_id>/update', methods=['POST'])(kitchen_update_order_status)
staff_bp.route('/driver', methods=['GET'])(driver_orders)
staff_bp.route('/driver/toggle-availability', methods=['POST'])(toggle_driver_availability)
staff_bp.route('/driver/orders/<int:order_id>/delivered', methods=['POST'])(update_delivery_status)