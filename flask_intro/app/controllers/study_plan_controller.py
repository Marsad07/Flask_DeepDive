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
    tasks = Task.query.filter_by(user_id=user_id).all()
    return render_template("studyplans/create_studyplan.html", tasks=tasks)

def store_plan():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("auth.login"))

    name = (request.form.get("title") or "Study Plan").strip()
    plan = StudyPlan(name=name, user_id=user_id)
    db.session.add(plan)
    db.session.commit()

    task_ids = request.form.getlist("task_ids")
    days = request.form.getlist("days")
    start_times = request.form.getlist("start_times")
    end_times = request.form.getlist("end_times")

    for i in range(len(task_ids)):
        if task_ids[i]:
            item = StudyPlanItem(
                plan_id=plan.id,
                task_id=int(task_ids[i]),
                day_of_week=days[i],
                start_time=start_times[i],
                end_time=end_times[i]
            )
            db.session.add(item)
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
