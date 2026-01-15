from flask import Blueprint
from app.controllers.general_controller import homepage, pomodoro, help_page

general_bp = Blueprint("general", __name__)

general_bp.route("/")(homepage)
general_bp.route("/pomodoro")(pomodoro)
general_bp.route("/help/")(help_page)
