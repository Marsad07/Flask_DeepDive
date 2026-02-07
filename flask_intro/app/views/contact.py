from flask import Blueprint, render_template
from app.controllers.email_controller import send_contact_email

contact_bp = Blueprint("contact", __name__)

@contact_bp.route("/contact")
def contact_page():
    return render_template("contact.html")

@contact_bp.route("/contact/send", methods=["POST"])
def send_email():
    return send_contact_email()