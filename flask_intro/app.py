from flask import Flask, render_template

tasks = [
    {"number": 1, "name": "Buy Milk", "description": "go to the shop", "date": "23/11/25"},
    {"number": 2, "name": "Homework", "description": "finish maths homework", "date": "23/11/25"},
    {"number": 3, "name": "Gym", "description": "train back and arms", "date": "24/11/25"},
]

app = Flask(__name__, template_folder='templates', static_folder='static')

@app.route("/")
def home():
    return render_template("tasks.html", tasks=tasks)

if __name__ == "__main__":
    app.run(debug=True)


