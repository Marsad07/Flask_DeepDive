from flask import render_template, session
from app.database import db

def homepage():
    user_id = session.get("user_id")
    if not user_id:
        return render_template("homepage.html", active_count=0, completed_count=0)

    cursor = db.cursor(dictionary=True)
    cursor.execute(
        "SELECT COUNT(*) AS active_count FROM tasks_new WHERE status='active' AND user_id=%s",
        (user_id,)
    )
    active_count = cursor.fetchone()["active_count"]

    cursor.execute(
        "SELECT COUNT(*) AS completed_count FROM tasks_new WHERE status='completed' AND user_id=%s",
        (user_id,)
    )
    completed_count = cursor.fetchone()["completed_count"]

    return render_template("homepage.html", active_count=active_count, completed_count=completed_count)

def pomodoro():
    return render_template("pomodoro_timer.html")

def help_page():
    return render_template("help_page.html")
