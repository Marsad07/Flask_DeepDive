from flask import Blueprint
from app.controllers.atlas_chat_controller import (
    atlas_hub,
    atlas_subject,
    atlas_generate
)

atlas_bp = Blueprint("atlas", __name__)

atlas_bp.route("/atlas", methods=["GET"])(atlas_hub)
atlas_bp.route("/subjects/<int:subject_id>/atlas", methods=["GET"])(atlas_subject)
atlas_bp.route("/subjects/<int:subject_id>/atlas/generate", methods=["POST"])(atlas_generate)
