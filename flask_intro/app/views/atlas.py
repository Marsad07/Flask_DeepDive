from flask import Blueprint
from app.controllers.atlas_chat_controller import (
    chat_page, chat_send, chat_new, chat_switch, chat_delete, chat_rename
)

atlas_bp = Blueprint("atlas", __name__)

atlas_bp.route("/atlas/chat", methods=["GET"])(chat_page)
atlas_bp.route("/atlas/chat/send", methods=["POST"])(chat_send)

atlas_bp.route("/atlas/chat/new", methods=["POST"])(chat_new)
atlas_bp.route("/atlas/chat/switch/<chat_id>", methods=["POST"])(chat_switch)
atlas_bp.route("/atlas/chat/delete/<chat_id>", methods=["POST"])(chat_delete)

atlas_bp.route("/atlas/chat/rename/<chat_id>", methods=["POST"])(chat_rename)
