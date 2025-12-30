from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime
import mysql.connector

db = mysql.connector.connect(
    host="localhost",
    user="root",
    passwd="PYTHONCOURSE",
    database="task_manager"
)

app = Flask(__name__, template_folder='templates', static_folder='static')

@app.route('/')
def homepage():
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT COUNT(*) AS active_count FROM tasks_new WHERE status = 'active'")
    active_count = cursor.fetchone()['active_count']

    cursor.execute("SELECT COUNT(*) AS completed_count FROM tasks_new WHERE status = 'completed'")
    completed_count = cursor.fetchone()['completed_count']

    return render_template('homepage.html', active_count=active_count, completed_count=completed_count)

@app.route("/tasks")
def tasks_page():
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM tasks_new WHERE status='active' ORDER BY due_date IS NULL, due_date ASC")
    tasks = cursor.fetchall()

    cursor.execute("SELECT * FROM tasks_new WHERE status = 'completed'")
    completed_tasks = cursor.fetchall()
    return render_template("tasks.html", tasks=tasks, completed_tasks=completed_tasks)

@app.route("/add_task_page")
def add_task_page():
    return render_template("add_tasks.html")

@app.route("/add", methods=["POST"])
def add_task():
    name = request.form["Task Name"]
    description = request.form["Task Description"]
    priority = request.form.get("priority")
    due_date = request.form["due_date"]

    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO tasks_new (task_name, task_description, priority, status, added_date, due_date) "
        "VALUES (%s, %s, %s, 'active', NOW(), %s)",
        (name, description, priority, due_date)
    )
    db.commit()
    return redirect(url_for("add_task_page"))

@app.route("/complete", methods=["POST"])
def complete_task():
    task_id = int(request.form["task_number"])
    cursor = db.cursor()
    cursor.execute(
        "UPDATE tasks_new SET status='completed', completed_date=NOW() WHERE id=%s",
        (task_id,)
    )
    db.commit()
    return redirect(url_for("tasks_page"))


@app.route("/clear_completed", methods=["POST"])
def clear_completed():
    cursor = db.cursor()
    cursor.execute("DELETE FROM tasks_new WHERE status='completed'")
    db.commit()
    return redirect(url_for("tasks_page"))


@app.route('/testdb')
def testdb():
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM tasks_new")
    tasks = cursor.fetchall()
    return str(tasks)

@app.route("/edit/<int:task_id>", methods=["GET", "POST"])
def edit_task(task_id):
    cursor = db.cursor(dictionary=True)
    if request.method == "POST":
        new_task_name = request.form["task_name"]
        new_task_description = request.form["task_description"]
        cursor.execute("UPDATE tasks_new SET task_name=%s, task_description=%s WHERE id=%s",
                       (new_task_name, new_task_description, task_id))
        db.commit()
        return redirect(url_for("tasks_page"))
    else:
        cursor.execute("SELECT * FROM tasks_new WHERE id=%s", (task_id,))
        task = cursor.fetchone()
        return render_template("edit.html", task=task)

if __name__ == "__main__":
    app.run(debug=True)