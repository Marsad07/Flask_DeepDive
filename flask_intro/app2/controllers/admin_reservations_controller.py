from app2.database import get_db
from flask import render_template, request, redirect, url_for

def edit_reservation(id):
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT * FROM reservations_restaurant WHERE customer_id=%s", (id,))
    reservation = cursor.fetchone()

    if reservation["status"] == "cancelled":
        return render_template(
            'admin/reservations/edit_reservations.html',
            reservation=reservation,
            cannot_edit=True
        )

    if request.method == 'POST':
        sql = """
            UPDATE reservations_restaurant
            SET customer_fullname=%s,
                customer_email=%s,
                customer_phonenum=%s,
                reservation_date=%s,
                reservation_time=%s,
                num_of_guests=%s,
                table_number=%s,
                special_requests=%s,
                status=%s
            WHERE customer_id=%s
        """

        values = (
            request.form['customer_fullname'],
            request.form['customer_email'],
            request.form['customer_phonenum'],
            request.form['reservation_date'],
            request.form['reservation_time'],
            request.form['num_of_guests'],
            request.form['table_number'],
            request.form['special_requests'],
            request.form['status'],
            id
        )

        cursor.execute(sql, values)
        db.commit()
        return redirect(url_for('admin.view_reservations'))

    return render_template(
        'admin/reservations/edit_reservations.html',
        reservation=reservation,
        cannot_edit=False
    )

def cancel_reservation(id):
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT status FROM reservations_restaurant WHERE customer_id=%s", (id,))
    reservation = cursor.fetchone()

    if reservation["status"] == "cancelled":
        return redirect(url_for('admin.view_reservations', already_cancelled=1))

    cursor.execute("UPDATE reservations_restaurant SET status='cancelled' WHERE customer_id=%s", (id,))
    db.commit()
    return redirect(url_for('admin.view_reservations'))
