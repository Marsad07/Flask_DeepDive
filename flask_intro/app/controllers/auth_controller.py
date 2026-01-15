from flask import render_template, request, redirect, url_for, session
from werkzeug.security import check_password_hash, generate_password_hash
from flask_intro.app.database import db, db3

def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        cursor = db3.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE user_name=%s", (username,))
        user = cursor.fetchone()

        if user and check_password_hash(user["user_password_hash"], password):
            session["user_id"] = user["user_id"]
            session["user_name"] = user["user_name"]
            return redirect("/tasks")

        return render_template("login.html", error="Invalid username or password")

    return render_template("login.html")

def logout():
    session.clear()
    return redirect(url_for("general.homepage"))

def register():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]
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

    return render_template("register.html")

def profile():
    user_id = session.get("user_id")
    if not user_id:
        return redirect("/login")

    cursor = db3.cursor(dictionary=True)
    cursor.execute(
        "SELECT user_name, user_email, created_date, last_login FROM users WHERE user_id=%s",
        (user_id,)
    )
    user = cursor.fetchone()

    cursor2 = db.cursor(dictionary=True)
    cursor2.execute("SELECT COUNT(*) AS total FROM tasks_new WHERE user_id=%s", (user_id,))
    total_tasks = cursor2.fetchone()["total"]

    cursor2.execute("SELECT COUNT(*) AS active FROM tasks_new WHERE user_id=%s AND status='active'", (user_id,))
    active_tasks = cursor2.fetchone()["active"]

    cursor2.execute("SELECT COUNT(*) AS completed FROM tasks_new WHERE user_id=%s AND status='completed'", (user_id,))
    completed_tasks = cursor2.fetchone()["completed"]

    return render_template(
        "profile_settings.html",
        user=user,
        total_tasks=total_tasks,
        active_tasks=active_tasks,
        completed_tasks=completed_tasks
    )

def update_details_page():
    user_id = session.get("user_id")
    if not user_id:
        return redirect("/login")

    cursor = db3.cursor(dictionary=True)
    cursor.execute("SELECT user_name, user_email FROM users WHERE user_id=%s", (user_id,))
    user = cursor.fetchone()

    return render_template("update_details.html", user=user)

def update_details():
    user_id = session.get("user_id")
    if not user_id:
        return redirect("/login")

    cursor = db3.cursor(dictionary=True)

    new_username = request.form.get("username")
    new_email = request.form.get("email")
    new_password = request.form.get("password")
    confirm = request.form.get("confirm")

    if new_username:
        cursor.execute("UPDATE users SET user_name=%s WHERE user_id=%s", (new_username, user_id))
        session["user_name"] = new_username

    if new_email:
        cursor.execute("UPDATE users SET user_email=%s WHERE user_id=%s", (new_email, user_id))

    if new_password or confirm:
        if new_password == confirm:
            hashed = generate_password_hash(new_password)
            cursor.execute(
                "UPDATE users SET user_password_hash=%s WHERE user_id=%s", (hashed, user_id)
            )
        else:
            return "Passwords do not match"

    db3.commit()
    return redirect("/profile")
