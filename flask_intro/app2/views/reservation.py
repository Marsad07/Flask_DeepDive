from flask import Blueprint
from app2.controllers.reservations_controller import reservations_page, cancel_reservation

reservations_bp = Blueprint("reservations", __name__, url_prefix="/reservations")

reservations_bp.route("/", methods=["GET", "POST"])(reservations_page)
reservations_bp.route('/reservation/cancel/<int:resv_id>',view_func=cancel_reservation,methods=['GET', 'POST'])