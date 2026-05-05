from flask import Blueprint, render_template
from app2.controllers.general_controller import (
    home_page, about_page, contact_page, newsletter_signup
)

general_bp = Blueprint("general", __name__)

general_bp.route("/")(home_page)
general_bp.route("/about")(about_page)
general_bp.route("/contact")(contact_page)
general_bp.route("/subscribe", methods=["POST"])(newsletter_signup)