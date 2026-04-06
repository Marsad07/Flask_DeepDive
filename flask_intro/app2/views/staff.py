from flask import Blueprint
from app2.controllers.staff_controller import staff_login, kitchen_display, staff_logout, kitchen_update_order_status

staff_bp = Blueprint('staff', __name__, url_prefix='/staff')

staff_bp.route('/login', methods=['GET', 'POST'])(staff_login)
staff_bp.route('/kitchen')(kitchen_display)
staff_bp.route('/logout')(staff_logout)
staff_bp.route('/kitchen/order/<int:order_id>/update', methods=['POST'])(kitchen_update_order_status)
