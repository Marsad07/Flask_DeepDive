from flask import Blueprint
from app2.controllers.cart_controller import (view_cart,
                                              order_now_menu,
                                              add_to_cart,
                                              remove_from_cart)


cart_bp = Blueprint("cart", __name__, url_prefix="/cart")

cart_bp.route("/")(view_cart)
cart_bp.route("/order-menu")(order_now_menu)
cart_bp.route("/add/<int:item_id>", methods=["POST"])(add_to_cart)
#cart_bp.route("/update/<int:item_id>", methods=["POST"])(update_cart)
cart_bp.route("/remove/<int:item_id>", methods=["POST"])(remove_from_cart)