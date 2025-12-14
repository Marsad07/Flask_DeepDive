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

@app.route("/")
def home():
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
    return redirect(url_for("home"))


@app.route("/complete", methods=["POST"])
def complete_task():
    task_id = int(request.form["task_number"])
    cursor = db.cursor()
    cursor.execute(
        "UPDATE tasks SET status='completed', completed_date=NOW() WHERE id=%s",
        (task_id,)
    )
    db.commit()
    return redirect(url_for("home"))


@app.route("/clear_completed", methods=["POST"])
def clear_completed():
    cursor = db.cursor()
    cursor.execute("DELETE FROM tasks WHERE status='completed'")
    db.commit()
    return redirect(url_for("home"))


@app.route('/testdb')
def testdb():
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM tasks")
    tasks = cursor.fetchall()
    return str(tasks)

if __name__ == "__main__":
    app.run(debug=True)