from flask import render_template, request, redirect, url_for, session, flash
from app.database import db, db3

def tasks_page():
    user_id = session["user_id"]
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT t.*, s.name AS subject_name
        FROM tasks_new t
        LEFT JOIN subjects s ON t.subject_id = s.id
        WHERE t.status='active' AND t.user_id=%s
        ORDER BY t.due_date IS NULL, t.due_date ASC
    """, (user_id,))
    tasks = cursor.fetchall()

    cursor.execute("""
        SELECT t.*, s.name AS subject_name
        FROM tasks_new t
        LEFT JOIN subjects s ON t.subject_id = s.id
        WHERE t.status='completed' AND t.user_id=%s
    """, (user_id,))
    completed_tasks = cursor.fetchall()

    return render_template("tasks.html", tasks=tasks, completed_tasks=completed_tasks)

def add_task_page():
    user_id = session.get("user_id")

    cursor = db3.cursor(dictionary=True)
    cursor.execute("SELECT id, name FROM subjects WHERE user_id=%s", (user_id,))
    subjects = cursor.fetchall()


    return render_template("add_tasks.html", subjects=subjects)

def add_task():
    name = request.form["Task Name"]
    description = request.form["Task Description"]
    priority = request.form.get("priority")
    subject_id = request.form.get("subject_id")
    due_date = request.form["due_date"]
    user_id = session["user_id"]

    cursor = db.cursor()
    cursor.execute("""
        INSERT INTO tasks_new (task_name, task_description, priority, status, added_date, due_date, user_id, subject_id)
        VALUES (%s, %s, %s, 'active', NOW(), %s, %s, %s)
    """, (name, description, priority, due_date, user_id, subject_id))
    db.commit()

    flash("Task added successfully")
    return redirect(url_for("tasks.add_task_page"))

def complete_task():
    task_id = int(request.form["task_number"])
    user_id = session["user_id"]

    cursor = db.cursor()
    cursor.execute("""
        UPDATE tasks_new
        SET status='completed', completed_date=NOW()
        WHERE id=%s AND user_id=%s
    """, (task_id, user_id))
    db.commit()

    return redirect(url_for("tasks.tasks_page"))

def clear_completed():
    user_id = session["user_id"]
    cursor = db.cursor()
    cursor.execute("DELETE FROM tasks_new WHERE status='completed' AND user_id=%s", (user_id,))
    db.commit()
    return redirect(url_for("tasks.tasks_page"))

def edit_task(id):
    user_id = session.get("user_id")

    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM tasks_new WHERE id=%s AND user_id=%s", (id, user_id))
    task = cursor.fetchone()

    if not task:
        return "Task not found"

    if request.method == "POST":
        title = request.form["title"]
        priority = request.form["priority"]
        due_date = request.form["due_date"]

        cursor.execute("""
            UPDATE tasks_new
            SET task_name=%s, priority=%s, due_date=%s
            WHERE id=%s AND user_id=%s
        """, (title, priority, due_date, id, user_id))

        db.commit()
        return redirect(url_for("subjects.subject_page",subject_id=task["subject_id"]))

    return render_template("edit.html", task=task)
