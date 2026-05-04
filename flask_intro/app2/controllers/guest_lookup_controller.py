from flask import render_template, request, redirect, url_for, session, Blueprint, Response, current_app, flash
from app2.database import get_db

def find_reservation():
    if request.method == "POST":
        email = request.form.get("email")
        phone = request.form.get("phone")

        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            SELECT * FROM reservations_restaurant
            WHERE customer_email = %s AND customer_phonenum = %s
            ORDER BY reservation_date DESC
        """, (email, phone))
        reservations = cursor.fetchall()
        cursor.close()
        db.close()

        return render_template("auth/guest_reservation.html",
                               reservations=reservations,
                               prefill_email=email,
                               prefill_phone=phone)

    return render_template("auth/find_reservation.html",
                           prefill_email=session.get('customer_email', ''),
                           prefill_phone=session.get('customer_phonenum', ''))