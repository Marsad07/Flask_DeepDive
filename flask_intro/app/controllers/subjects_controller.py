from flask import render_template, request, redirect, session, url_for
from flask_intro.app.database import db, db3

def subjects():
    user_id = session.get("user_id")

    cursor = db3.cursor(dictionary=True)
    cursor.execute("SELECT * FROM subjects WHERE user_id=%s", (user_id,))
    subjects_list = cursor.fetchall()

    return render_template("subjects.html", subjects=subjects_list)

def subject_page(subject_id):
    user_id = session.get("user_id")

    cursor = db3.cursor(dictionary=True)
    cursor.execute("SELECT * FROM subjects WHERE id=%s AND user_id=%s", (subject_id, user_id))
    subject = cursor.fetchone()

    cursor2 = db.cursor(dictionary=True)
    cursor2.execute("SELECT * FROM tasks_new WHERE subject_id=%s AND user_id=%s", (subject_id, user_id))
    tasks = cursor2.fetchall()

    completed = sum(1 for task in tasks if task["status"] == "completed")
    total = len(tasks)
    progress = int((completed / total) * 100) if total > 0 else 0

    return render_template("subject_content.html", subject=subject, tasks=tasks, progress=progress)

def add_subject_page():
    return render_template("add_subject_page.html")

def add_subject():
    user_id = session.get("user_id")
    if not user_id:
        return redirect("/login")

    name = request.form["name"]
    color = request.form["color"]
    description = request.form.get("description") or ""
    study_goal = request.form.get("study_goal") or ""

    cursor = db3.cursor()
    cursor.execute("""
        INSERT INTO subjects (user_id, name, color, description, study_goal)
        VALUES (%s, %s, %s, %s, %s)
    """, (user_id, name, color, description, study_goal))
    db3.commit()

    return redirect("/subjects")

def add_task_subject(subject_id):
    user_id = session.get("user_id")
    title = request.form["title"]

    cursor = db.cursor()
    cursor.execute("""
        INSERT INTO tasks_new (title, status, user_id, subject_id)
        VALUES (%s, 'active', %s, %s)
    """, (title, user_id, subject_id))
    db.commit()

    return redirect(f"/subjects/{subject_id}")

def complete_task_subject(subject_id):
    user_id = session.get("user_id")
    task_id = request.form.get("task_id")

    cursor = db.cursor()
    cursor.execute("""
        UPDATE tasks_new
        SET status='completed', completed_date=NOW()
        WHERE id=%s AND user_id=%s AND subject_id=%s
    """, (task_id, user_id, subject_id))
    db.commit()

    return redirect(f"/subjects/{subject_id}")

def delete_task_subject(subject_id):
    user_id = session.get("user_id")
    task_id = request.form.get("task_id")

    cursor = db.cursor()
    cursor.execute("""
        DELETE FROM tasks_new
        WHERE id=%s AND user_id=%s AND subject_id=%s
    """, (task_id, user_id, subject_id))
    db.commit()

    return redirect(f"/subjects/{subject_id}")

def edit_subject(id):
    user_id = session.get("user_id")
    cursor = db3.cursor(dictionary=True)

    if request.method == "POST":
        name = request.form["name"]
        description = request.form["description"]
        color = request.form["color"]
        cursor.execute("""
            UPDATE subjects
            SET name=%s, description=%s, color=%s
            WHERE id=%s AND user_id=%s
        """, (name, description, color, id, user_id))
        db3.commit()
        return redirect("/subjects")

    cursor.execute("SELECT * FROM subjects WHERE id=%s AND user_id=%s", (id, user_id))
    subject = cursor.fetchone()

    return render_template("edit_subject.html", subject=subject)

def notes_page(subject_id):
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("auth.login"))

    cursor = db3.cursor(dictionary=True)
    cursor.execute("SELECT * FROM subjects WHERE id=%s AND user_id=%s", (subject_id, user_id))
    subject = cursor.fetchone()

    if not subject:
        return "Subject not found", 404

    return render_template("subject_notepad.html", subject=subject)

def save_notes(subject_id):
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("auth.login"))

    notes = request.form.get("notes", "")
    cursor = db3.cursor()
    cursor.execute("""
        UPDATE `task_manager`.`subjects`
        SET `notes`=%s
        WHERE `id`=%s AND `user_id`=%s
    """, (notes, subject_id, user_id))
    db3.commit()

    return redirect(url_for("subjects.subject_page", subject_id=subject_id))