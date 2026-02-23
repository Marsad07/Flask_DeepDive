from flask import render_template, request, redirect, url_for, flash
from datetime import date

def reservations_page():
    if request.method == "POST":
        name = request.form.get("fullname")
        email = request.form.get("email")
        phone = request.form.get("phoneNum")
        resv_date = request.form.get("resv_date")
        resv_time = request.form.get("resv_time")
        guests = request.form.get("guests_num")
        table = request.form.get("table_num")
        special_requests = request.form.get("special_requests")

        if not all([name, email, phone, resv_date, resv_time, guests]):
            return "All fields required!", 400


        return f"Reservation confirmed for {name} on {resv_date} at {resv_time} for {guests} guests!"

    today = date.today().isoformat()
    return render_template("reservations.html", today=today)