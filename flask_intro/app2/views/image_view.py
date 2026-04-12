from flask import Blueprint, render_template
from app2.controllers.image_manager_controller import image_manager_controller

image_bp = Blueprint("image", __name__, url_prefix="/admin")

@image_bp.route("/images", methods=["GET", "POST"])
def image_manager():
    context = image_manager_controller()
    if isinstance(context, dict):
        return render_template("admin/image_manager.html", **context)
    return context