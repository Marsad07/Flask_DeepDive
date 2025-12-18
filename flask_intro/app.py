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
    cursor.execute("SELECT COUNT(*) AS active_count FROM tasks WHERE status = 'active'")
    active_count = cursor.fetchone()['active_count']

    cursor.execute("SELECT COUNT(*) AS completed_count FROM tasks WHERE status = 'completed'")
    completed_count = cursor.fetchone()['completed_count']

    return render_template('homepage.html', active_count=active_count, completed_count=completed_count)

@app.route("/tasks")
def tasks_page():
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM tasks WHERE status='active'")
    tasks = cursor.fetchall()

    cursor.execute("SELECT * FROM tasks WHERE status = 'completed'")
    completed_tasks = cursor.fetchall()
    return render_template("tasks.html", tasks=tasks, completed_tasks=completed_tasks)

@app.route("/add", methods=["POST"])
def add_task():
    name = request.form["Task Name"]
    description = request.form["Task Description"]

    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO tasks (task_name, task_description, status, added_date) VALUES (%s, %s, 'active', NOW())",
        (name, description)
    )
    db.commit()
    return redirect(url_for("tasks_page"))


@app.route("/complete", methods=["POST"])
def complete_task():
    task_id = int(request.form["task_number"])
    cursor = db.cursor()
    cursor.execute(
        "UPDATE tasks SET status='completed', completed_date=NOW() WHERE id=%s",
        (task_id,)
    )
    db.commit()
    return redirect(url_for("tasks_page"))


@app.route("/clear_completed", methods=["POST"])
def clear_completed():
    cursor = db.cursor()
    cursor.execute("DELETE FROM tasks WHERE status='completed'")
    db.commit()
    return redirect(url_for("tasks_page"))


@app.route('/testdb')
def testdb():
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM tasks")
    tasks = cursor.fetchall()
    return str(tasks)

@app.route("/edit/<int:task_id>", methods=["GET", "POST"])
def edit_task(task_id):
    cursor = db.cursor(dictionary=True)
    if request.method == "POST":
        new_task_name = request.form["task_name"]
        new_task_description = request.form["task_description"]
        cursor.execute("UPDATE tasks SET task_name=%s, task_description=%s WHERE id=%s",
                       (new_task_name, new_task_description, task_id))
        db.commit()
        return redirect(url_for("tasks_page"))
    else:
        cursor.execute("SELECT * FROM tasks WHERE id=%s", (task_id,))
        task = cursor.fetchone()
        return render_template("edit.html", task=task)

if __name__ == "__main__":
    app.run(debug=True)