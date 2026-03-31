from flask import Blueprint
from app2.controllers.order_tracking_controller import track_order

orders_bp = Blueprint("orders", __name__)

orders_bp.add_url_rule('/orders/track/<order_number>',
    view_func=track_order,
    methods=['GET', 'POST']
)