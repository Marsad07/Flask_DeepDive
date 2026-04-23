from flask import Blueprint
from app2.controllers.guest_lookup_controller import find_reservation

guest_lookup_bp = Blueprint("guest_lookup", __name__, url_prefix="/guest")


guest_lookup_bp.route("/find_reservation", methods=["GET", "POST"])(find_reservation)
