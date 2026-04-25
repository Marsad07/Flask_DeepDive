from flask import Blueprint
from app2.controllers.reservations_controller import (reservations_page, cancel_reservation, modify_reservation,
                                                      cancel_page, guest_find_reservation, guest_view_reservation,
                                                      my_reservations, guest_modify_reservation)

reservations_bp = Blueprint("reservations", __name__, url_prefix="/reservations")
reservations_bp.route("/my-reservations", methods=["GET"])(my_reservations)
reservations_bp.route("/", methods=["GET", "POST"])(reservations_page)
reservations_bp.route('/reservation/cancel/<int:resv_id>', methods=['GET', 'POST'])(cancel_reservation)
reservations_bp.route("/modify/<int:resv_id>", methods=["GET", "POST"])(modify_reservation)
reservations_bp.route('/cancel/<int:resv_id>', methods=['GET'])(cancel_page)
reservations_bp.route("/guest/find", methods=["GET", "POST"])(guest_find_reservation)
reservations_bp.route("/guest/view/<int:resv_id>", methods=["GET"])(guest_view_reservation)
reservations_bp.route("/guest/modify/<int:resv_id>", methods=["GET", "POST"])(guest_modify_reservation)

