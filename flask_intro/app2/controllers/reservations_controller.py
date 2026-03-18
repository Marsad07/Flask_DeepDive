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
        resv_date = request.form.get("resv_date")
        resv_time = request.form.get("resv_time")
        guests = request.form.get("guests_num")
        table = request.form.get("table_num")
        special_requests = request.form.get("special_requests")

        cursor = restaurant_db1.cursor()

        # This query checks if the tables already booked
        cursor.execute("""
            SELECT * FROM reservations_restaurant 
            WHERE table_number = %s 
            AND reservation_date = %s 
            AND reservation_time = %s
            AND reservation_status != 'Cancelled'
        """, (table, resv_date, resv_time))

        existing_booking = cursor.fetchone()

        if existing_booking:
            # To show the table is taken
            today = date.today().isoformat()
            error_message = "Sorry, this table is already booked for that time. Please select another table."
            return render_template("reservations.html", today=today, error=error_message)

        # To show that this table is available and the user can proceed with the booking
        cursor.execute("""INSERT INTO reservations_restaurant 
            (customer_fullname, customer_email, customer_phonenum, reservation_date, 
             reservation_time, num_of_guests, table_number, special_requests) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                       (name, email, phone, resv_date, resv_time, guests, table, special_requests))
        restaurant_db1.commit()
        return render_template("reservation_success.html", name=name, email=email,
                               date=resv_date, time=resv_time, guests=guests, table=table)

    today = date.today().isoformat()
    return render_template("reservations.html", today=today)
