from flask import Blueprint
from app2.controllers.reservations_controller import reservations_page

reservations_bp = Blueprint("reservations", __name__, url_prefix="/reservations")

reservations_bp.route("/", methods=["GET", "POST"])(reservations_page)
