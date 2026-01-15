from flask import Blueprint
from app.controllers.tasks_controller import (
    tasks_page, add_task_page, add_task, complete_task, clear_completed, edit_task
)

tasks_bp = Blueprint("tasks", __name__)

tasks_bp.route("/tasks")(tasks_page)
tasks_bp.route("/add_task_page")(add_task_page)
tasks_bp.route("/add", methods=["POST"])(add_task)
tasks_bp.route("/complete", methods=["POST"])(complete_task)
tasks_bp.route("/clear_completed", methods=["POST"])(clear_completed)
tasks_bp.route("/edit_task/<int:id>", methods=["GET", "POST"])(edit_task)
