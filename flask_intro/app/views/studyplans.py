from flask import Blueprint, render_template, session, redirect, url_for, request
from app.models.studyplan import (
    get_plans_for_user,
    create_plan,
    get_plan,
    get_plan_items,
    generate_items_for_plan,
    delete_plan,
    get_tasks_for_user
)

studyplans_bp = Blueprint("studyplans", __name__, url_prefix="/studyplans")


@studyplans_bp.route("/")
def index():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("auth.login"))

    plans = get_plans_for_user(user_id)
    return render_template("studyplans/index.html", plans=plans)


@studyplans_bp.route("/create", methods=["GET", "POST"])
def create():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        title = (request.form.get("title") or "New Study Plan").strip()
        task_ids = request.form.getlist("task_ids")

        plan_id = create_plan(user_id, title[:60])
        generate_items_for_plan(user_id, plan_id, task_ids)
        return redirect(url_for("studyplans.show", plan_id=plan_id))

    tasks = get_tasks_for_user(user_id)
    return render_template("studyplans/create_studyplan.html", tasks=tasks)


@studyplans_bp.route("/<int:plan_id>")
def show(plan_id):
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("auth.login"))

    plan = get_plan(user_id, plan_id)
    if not plan:
        return "Plan not found", 404

    items = get_plan_items(user_id, plan_id)
    return render_template(
        "studyplans/show_studyplan.html",
        plan=plan,
        items=items
    )

@studyplans_bp.route("/<int:plan_id>/delete", methods=["POST"])
def delete(plan_id):
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("auth.login"))
    delete_plan(user_id, plan_id)
    return redirect(url_for("studyplans.index"))

