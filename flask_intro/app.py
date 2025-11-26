from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime

tasks = [
    {"number": 1, "name": "Buy Milk", "description": "go to the shop", "date": "23/11/25", "completed": False},
    {"number": 2, "name": "Homework", "description": "finish maths homework", "date": "23/11/25", "completed": False},
    {"number": 3, "name": "Gym", "description": "train back and arms", "date": "24/11/25", "completed": False},
]
completed_tasks = []

app = Flask(__name__, template_folder='templates', static_folder='static')

@app.route("/")
def home():
    return render_template("tasks.html", tasks=tasks, completed_tasks=completed_tasks)

@app.route("/add", methods=["POST"])
def add_task():
    name = request.form["Task Name"]
    description = request.form["Task Description"]
    tasks.append({
        "number": len(tasks) + 1,
        "name": name,
        "description": description,
        "date": datetime.now().strftime("%m/%d/%Y"),
        "completed": False
    })
    return redirect(url_for("home"))

@app.route("/complete", methods=["POST"])
def complete_task():
    task_number = int(request.form["task_number"])
    for task in tasks:
        if task["number"] == task_number:
            task["completed"] = True
            completed_tasks.append(task)
            tasks.remove(task)
            break
    return redirect(url_for("home"))

if __name__ == "__main__":
    app.run(debug=True)