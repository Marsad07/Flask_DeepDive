from flask import Flask, render_template, request, redirect, url_for, session, flash
from datetime import datetime
import mysql.connector
from werkzeug.security import check_password_hash, generate_password_hash

db = mysql.connector.connect(
    host="localhost",
    user="root",
    passwd="PYTHONCOURSE",
    database="task_manager"
)

db3 = mysql.connector.connect(
    host="localhost",
    user="root",
    passwd="PYTHONCOURSE",
    database="subject_manager_2"
)

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = "ajd82h9d8ahd92h9ahd92h9ahd92h9ahd9"

@app.route('/')
def homepage():
    user_id = session.get('user_id')
    if not user_id:
        return render_template('homepage.html', active_count=0, completed_count=0)

    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT COUNT(*) AS active_count FROM tasks_new WHERE status='active' AND user_id=%s", (user_id,))
    active_count = cursor.fetchone()['active_count']

    cursor.execute("SELECT COUNT(*) AS completed_count FROM tasks_new WHERE status='completed' AND user_id=%s", (user_id,))
    completed_count = cursor.fetchone()['completed_count']

    return render_template('homepage.html', active_count=active_count, completed_count=completed_count)

@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cursor = db3.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE user_name=%s", (username,))
        user = cursor.fetchone()

        if user and check_password_hash(user["user_password_hash"], password):
            session['user_id'] = user["user_id"]
            session['user_name'] = user["user_name"]
            return redirect("/tasks")

        return render_template('login.html', error="Invalid username or password")

    return render_template('login.html')

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("homepage"))

@app.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        hashed = generate_password_hash(password)

        cursor = db3.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE user_name=%s", (username,))
        user = cursor.fetchone()

        if user:
            return "An account with this username already exists."

        cursor.execute("""
            INSERT INTO users (user_name, user_email, user_password_hash, created_date)
            VALUES (%s, %s, %s, NOW())
        """, (username, email, hashed))
        db3.commit()

        return redirect("/login")

    return render_template('register.html')

@app.route("/profile")
def profile():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for("login"))

    cursor = db3.cursor(dictionary=True)
    cursor.execute("SELECT user_name, user_email, created_date, last_login FROM users WHERE user_id=%s", (user_id,))
    user = cursor.fetchone()

    cursor2 = db.cursor(dictionary=True)
    cursor2.execute("SELECT COUNT(*) AS total FROM tasks_new WHERE user_id=%s", (user_id,))
    total_tasks = cursor2.fetchone()['total']

    cursor2.execute("SELECT COUNT(*) AS active FROM tasks_new WHERE user_id=%s AND status='active'", (user_id,))
    active_tasks = cursor2.fetchone()['active']

    cursor2.execute("SELECT COUNT(*) AS completed FROM tasks_new WHERE user_id=%s AND status='completed'", (user_id,))
    completed_tasks = cursor2.fetchone()['completed']

    return render_template("profile_settings.html",
                           user=user,
                           total_tasks=total_tasks,
                           active_tasks=active_tasks,
                           completed_tasks=completed_tasks)

@app.route("/tasks")
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

@app.route("/add_task_page")
def add_task_page():
    user_id = session.get("user_id")

    cursor = db3.cursor(dictionary=True)
    cursor.execute("SELECT id, name FROM subjects WHERE user_id=%s", (user_id,))
    subjects = cursor.fetchall()

    return render_template("add_tasks.html", subjects=subjects)

@app.route("/add", methods=["POST"])
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
    return redirect(url_for("add_task_page"))

@app.route("/complete", methods=["POST"])
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

    return redirect(url_for("tasks_page"))

@app.route("/clear_completed", methods=["POST"])
def clear_completed():
    user_id = session["user_id"]
    cursor = db.cursor()
    cursor.execute("DELETE FROM tasks_new WHERE status='completed' AND user_id=%s", (user_id,))
    db.commit()
    return redirect(url_for("tasks_page"))

@app.route("/subjects")
def subjects():
    user_id = session.get("user_id")

    cursor = db3.cursor(dictionary=True)
    cursor.execute("SELECT * FROM subjects WHERE user_id=%s", (user_id,))
    subjects = cursor.fetchall()

    return render_template("subjects.html", subjects=subjects)

@app.route("/subjects/<int:subject_id>")
def subject_page(subject_id):
    user_id = session.get("user_id")

    cursor = db3.cursor(dictionary=True)
    cursor.execute("SELECT * FROM subjects WHERE id=%s AND user_id=%s", (subject_id, user_id))
    subject = cursor.fetchone()

    cursor2 = db.cursor(dictionary=True)
    cursor2.execute("SELECT * FROM tasks_new WHERE subject_id=%s AND user_id=%s", (subject_id, user_id))
    tasks = cursor2.fetchall()

    return render_template("subject_content.html", subject=subject, tasks=tasks)

@app.route("/add_subject", methods=["POST"])
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

@app.route("/subjects/<int:subject_id>/add_task", methods=['POST'])
def add_task_subject(subject_id):
    user_id = session.get("user_id")
    title = request.form['title']

    cursor = db.cursor()
    cursor.execute("""
        INSERT INTO tasks_new (title, status, user_id, subject_id)
        VALUES (%s, 'active', %s, %s)
    """, (title, user_id, subject_id))
    db.commit()

    return redirect(f"/subjects/{subject_id}")

@app.route('/pomodoro')
def pomodoro():
    return render_template("pomodoro_timer.html")

@app.route("/update_details_page")
def update_details_page():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login"))

    cursor = db3.cursor(dictionary=True)
    cursor.execute("SELECT user_name, user_email FROM users WHERE user_id=%s", (user_id,))
    user = cursor.fetchone()

    return render_template("update_details.html", user=user)

@app.route("/update_details", methods=['POST'])
def update_details():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for("login"))

    cursor = db3.cursor(dictionary=True)

    new_username = request.form.get('username')
    new_email = request.form.get('email')
    new_password = request.form.get('password')
    confirm = request.form.get('confirm')

    if new_username:
        cursor.execute("UPDATE users SET user_name=%s WHERE user_id=%s", (new_username, user_id))
        session['user_name'] = new_username

    if new_email:
        cursor.execute("UPDATE users SET user_email=%s WHERE user_id=%s", (new_email, user_id))

    if new_password or confirm:
        if new_password == confirm:
            hashed = generate_password_hash(new_password)
            cursor.execute(
                "UPDATE users SET user_password_hash=%s WHERE user_id=%s", (hashed, user_id))
        else:
            return "Passwords do not match"

    db3.commit()
    return redirect(url_for("profile"))

@app.route("/subjects/<int:subject_id>/complete_task", methods=["POST"])
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

@app.route("/subjects/<int:subject_id>/delete_task", methods=["POST"])
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

@app.context_processor
def inject_subjects():
    user_id = session.get("user_id")
    if not user_id:
        return dict(sidebar_subjects=[])

    cursor = db3.cursor(dictionary=True)
    cursor.execute("SELECT id, name FROM subjects WHERE user_id=%s", (user_id,))
    subjects = cursor.fetchall()

    return dict(sidebar_subjects=subjects)


if __name__ == "__main__":
    app.run(debug=True)
