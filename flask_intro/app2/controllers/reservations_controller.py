from flask import render_template, request, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from app2.database import restaurant_db1
from datetime import date
today = date.today().isoformat()

def reservations_page():
    if request.method == "POST":
        name = request.form.get("fullname")
        email = request.form.get("email")
        phone = request.form.get("phoneNum")
        date = request.form.get("resv_date")
        time = request.form.get("resv_time")
        guests = request.form.get("guests_num")
        table = request.form.get("table_num")
        requests = request.form.get("special_requests")

        cursor = restaurant_db1.cursor()
        cursor.execute("INSERT INTO reservations_restaurant (customer_fullname, customer_email, customer_phonenum, "
                       "reservation_date, reservation_time, num_of_guests, table_number, special_requests)"
                       "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", (name, email, phone, date, time, guests,
                                                                   table, requests))
        restaurant_db1.commit()

        return render_template("reservation_success.html",
                               name=name,
                               email=email,
                               date=date,
                               time=time,
                               guests=guests,
                               table=table,
                               )

    return render_template("reservations.html", today=today)
