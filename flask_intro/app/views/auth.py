from flask import Blueprint
from app.controllers.auth_controller import (
    login, logout, register, profile, update_details_page, update_details
)

auth_bp = Blueprint("auth", __name__)

auth_bp.route("/login", methods=["GET", "POST"])(login)
auth_bp.route("/logout")(logout)
auth_bp.route("/register", methods=["GET", "POST"])(register)
auth_bp.route("/profile")(profile)

auth_bp.route("/update_details_page")(update_details_page)
auth_bp.route("/update_details", methods=["POST"])(update_details)