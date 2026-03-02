from flask import render_template, request, redirect, url_for, flash


def reservations_page():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        phone = request.form.get("phone")
        date = request.form.get("date")
        time = request.form.get("time")
        guests = request.form.get("guests")

        flash(f"Reservation confirmed for {name}!", "success")
        return redirect(url_for("reservations.reservations_page"))

    return render_template("reservations.html")
