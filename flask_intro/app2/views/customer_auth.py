from flask import Blueprint
from app2.controllers.customer_auth_controller import (customer_login, customer_register,
                                                        customer_logout, customer_dashboard,
                                                       customer_profile_settings, update_profile)

customer_auth_bp = Blueprint("customer_auth", __name__, url_prefix="/auth")

customer_auth_bp.route("/login", methods=["GET", "POST"], endpoint="login")(customer_login)
customer_auth_bp.route("/register", methods=["GET", "POST"], endpoint="register")(customer_register)
customer_auth_bp.route("/logout", endpoint="logout")(customer_logout)
customer_auth_bp.route("/dashboard", endpoint="customer_dashboard")(customer_dashboard)
customer_auth_bp.route("/profile", endpoint="customer_profile")(customer_profile_settings)
customer_auth_bp.route("/profile/update", methods=["POST"], endpoint="update_profile")(customer_profile_settings)