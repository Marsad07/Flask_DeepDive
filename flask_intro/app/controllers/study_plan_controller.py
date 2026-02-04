from flask import render_template, session, redirect, url_for, request
from app.database import db
from app.models.studyplan import StudyPlan, StudyPlanItem
from app.models.task import Task

def index():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("auth.login"))

    plans = StudyPlan.query.filter_by(user_id=user_id).order_by(StudyPlan.id.desc()).all()
    return render_template("studyplans/index.html", plans=plans)

def create_studyplan():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("auth.login"))
    return render_template("studyplans/create_studyplan.html")

def store_plan():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("auth.login"))

    name = (request.form.get("name") or "Study Plan").strip()

    plan = StudyPlan(name=name, user_id=user_id)
    db.session.add(plan)
    db.session.commit()

    return redirect(url_for("studyplans.generate_plan", plan_id=plan.id))

def generate_plan(plan_id):
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("auth.login"))

    plan = StudyPlan.query.filter_by(id=plan_id, user_id=user_id).first()
    if not plan:
        return "Plan not found", 404

    tasks = Task.query.filter_by(user_id=user_id).all()

    StudyPlanItem.query.filter_by(plan_id=plan.id).delete()

    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    day_index = 0

    for task in tasks:
        item = StudyPlanItem(
            plan_id=plan.id,
            day_of_week=days[day_index],
            start_time="10:00",
            end_time="11:00",
            task_id=task.id
        )
        db.session.add(item)
        day_index = (day_index + 1) % len(days)

    db.session.commit()
    return redirect(url_for("studyplans.show_studyplan", plan_id=plan.id))

def show_studyplan(plan_id):
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("auth.login"))

    plan = StudyPlan.query.filter_by(id=plan_id, user_id=user_id).first()
    if not plan:
        return "Plan not found", 404

    items = StudyPlanItem.query.filter_by(plan_id=plan.id).order_by(StudyPlanItem.id.asc()).all()
    return render_template("studyplans/show_studyplan.html", plan=plan, items=items)

def delete_studyplan(plan_id):
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("auth.login"))

    plan = StudyPlan.query.filter_by(id=plan_id, user_id=user_id).first()
    if plan:
        StudyPlanItem.query.filter_by(plan_id=plan.id).delete()
        db.session.delete(plan)
        db.session.commit()

    return redirect(url_for("studyplans.index"))
