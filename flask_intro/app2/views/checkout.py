from flask import Blueprint, jsonify
from app2.controllers.checkout_controller import (checkout_page, process_order, order_confirmation,
                                                  create_payment_intent,)


checkout_bp = Blueprint("checkout", __name__, url_prefix="/checkout")

checkout_bp.route("/")(checkout_page)
checkout_bp.route("/process", methods=["POST"])(process_order)
checkout_bp.route("/confirmation/<order_number>")(order_confirmation)
checkout_bp.route('/create-payment-intent', methods=['POST'])(lambda: jsonify(create_payment_intent()))
