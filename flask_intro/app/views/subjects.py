from flask import Blueprint
from app.controllers.subjects_controller import (
    subjects, subject_page, add_subject_page, add_subject,
    add_task_subject, complete_task_subject, delete_task_subject, edit_subject,
    notes_page, save_notes
)

subjects_bp = Blueprint("subjects", __name__)

subjects_bp.route("/subjects")(subjects)
subjects_bp.route("/subjects/<int:subject_id>")(subject_page)

subjects_bp.route("/add_subject_page")(add_subject_page)
subjects_bp.route("/add_subject", methods=["POST"])(add_subject)

subjects_bp.route("/subjects/<int:subject_id>/add_task", methods=["POST"])(add_task_subject)
subjects_bp.route("/subjects/<int:subject_id>/complete_task", methods=["POST"])(complete_task_subject)
subjects_bp.route("/subjects/<int:subject_id>/delete_task", methods=["POST"])(delete_task_subject)

subjects_bp.route("/subjects/<int:id>/edit", methods=["GET", "POST"])(edit_subject)

subjects_bp.route("/subjects/<int:subject_id>/notes", methods=["GET"])(notes_page)
subjects_bp.route("/subjects/<int:subject_id>/save_notes", methods=["POST"])(save_notes)
