from flask import Blueprint
from app2.controllers.menu_controller import show_menu

menu_bp = Blueprint("menu", __name__, url_prefix="/menu")

menu_bp.route("/")(show_menu)