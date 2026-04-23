from flask import render_template, request, redirect, url_for, flash
from requests import session
from app2.database import get_db, staff_redirect
from datetime import date
from app2 import socketio

@staff_redirect
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

        db = get_db()
        cursor = db.cursor(dictionary=True)

        # This query checks if the table is already booked
        cursor.execute("""
            SELECT * FROM reservations_restaurant 
            WHERE table_number = %s 
            AND reservation_date = %s 
            AND reservation_time = %s
            AND reservation_status != 'Cancelled'
        """, (table, resv_date, resv_time))

        existing_booking = cursor.fetchone()

        if existing_booking:
            cursor.close()
            db.close()
            cursor2 = get_db().cursor(dictionary=True)
            cursor2.execute("SELECT * FROM restaurant_customer_tables WHERE is_active = TRUE ORDER BY table_number ASC")
            tables = cursor2.fetchall()
            cursor2.close()
            today = date.today().isoformat()
            return render_template("reservations.html", today=today, tables=tables,
                                   error="Sorry,"
                                         " this table is already booked for that time. Please select another table.")

        # Table is available so insert the booking
        cursor.execute("""INSERT INTO reservations_restaurant 
            (customer_fullname, customer_email, customer_phonenum, reservation_date, 
             reservation_time, num_of_guests, table_number, special_requests) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                       (name, email, phone, resv_date, resv_time, guests, table, special_requests))
        db.commit()
        cursor.close()
        db.close()

        socketio.emit('table_unavailable', {
            'table_num': table
        }, broadcast=True)

        # Send confirmation email
        try:
            from app2 import mail
            from flask_mailman import EmailMessage
            html_body = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        @media (prefers-color-scheme: dark) {{
            .email-body {{ background-color: #1A1410 !important; color: #FFFEF2 !important; }}
            .order-ref-box {{ background-color: #2C2416 !important; }}
            p {{ color: #FFFEF2 !important; }}
        }}
    </style>
</head>
<body bgcolor="#F8F4EC" style="margin: 0; padding: 0;">
    <table width="100%" bgcolor="#F8F4EC" cellpadding="0" cellspacing="0" border="0">
        <tr>
            <td align="center" style="padding: 40px 20px;">
                <table width="600" cellpadding="0" cellspacing="0" border="0" style="max-width: 600px; width: 100%;">

                    <!-- Header -->
                    <tr>
                        <td bgcolor="#2C2416" align="center" style="padding: 30px; border-radius: 12px 12px 0 0;">
                            <h1 style="color: #FFD700; margin: 0;
                             font-size: 28px; letter-spacing: 3px; font-family: Georgia, serif;">
                                RESTAURANT NAME
                            </h1>
                            <p style="color: #D4AF37; margin: 8px 0 0 0; font-size: 14px; letter-spacing: 2px;
                             font-family: Georgia, serif;">
                                RESERVATION CONFIRMATION
                            </p>
                        </td>
                    </tr>

                    <!-- Body -->
                    <tr>
                        <td bgcolor="#FFFFFF" style="padding: 30px;">
                            <p style="color: #2C2416; font-size: 16px;
                             font-family: Georgia, serif; margin: 0 0 10px 0;">
                                Hi <strong>{name}</strong>,
                            </p>
                            <p style="color: #5C4033; font-size: 15px; line-height: 1.6;
                             font-family: Georgia, serif; margin: 0 0 20px 0;">
                                Your table has been reserved! We look forward to welcoming you.
                            </p>

                            <!-- Reservation details box -->
                            <table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin: 0 0 20px 0;">
                                <tr>
                                    <td bgcolor="#F8F4EC" style="padding: 15px 20px;
                                     border-radius: 8px; border-left: 4px solid #8B0000;">
                                        <p style="margin: 0; color: #5C4033; font-size: 13px;
                                         font-family: Georgia, serif; letter-spacing: 1px;">
                                            RESERVATION DETAILS
                                        </p>
                                    </td>
                                </tr>
                            </table>

                            <table width="100%" cellpadding="0" cellspacing="0" border="0">
                                <tr>
                                    <td style="padding: 10px 0; color: #5C4033; font-size: 14px;
                                     font-family: Georgia, serif; border-bottom: 1px solid #E8DFD0;">
                                        Date
                                    </td>
                                    <td align="right" style="padding: 10px 0; color: #2C2416; font-weight: bold;
                                     font-size: 14px; font-family: Georgia, serif; border-bottom: 1px solid #E8DFD0;">
                                        {resv_date}
                                    </td>
                                </tr>
                                <tr>
                                    <td style="padding: 10px 0; color: #5C4033; font-size: 14px; font-family: Georgia,
                                     serif; border-bottom: 1px solid #E8DFD0;">
                                        Time
                                    </td>
                                    <td align="right" style="padding: 10px 0; color: #2C2416;
                                     font-weight: bold; font-size: 14px; font-family: Georgia, serif;
                                      border-bottom: 1px solid #E8DFD0;">
                                        {resv_time}
                                    </td>
                                </tr>
                                <tr>
                                    <td style="padding: 10px 0; color: #5C4033;
                                     font-size: 14px; font-family: Georgia, serif; border-bottom: 1px solid #E8DFD0;">
                                        Guests
                                    </td>
                                    <td align="right" style="padding: 10px 0; color: #2C2416;
                                     font-weight: bold; font-size: 14px; font-family: Georgia, serif;
                                      border-bottom: 1px solid #E8DFD0;">
                                        {guests}
                                    </td>
                                </tr>
                                <tr>
                                    <td style="padding: 10px 0; color: #5C4033; font-size: 14px;
                                     font-family: Georgia, serif;">
                                        Table
                                    </td>
                                    <td align="right" style="padding: 10px 0; color: #8B0000; font-weight: bold;
                                     font-size: 18px; font-family: Georgia, serif;">
                                        Table {table}
                                    </td>
                                </tr>
                            </table>
                            <p style="margin-top: 20px;">
                                Need to cancel?  
                                <a href="{{ url_for('reservations.cancel_reservation',
                                 resv_id=reservation_id, _external=True) }}">
                                    Click here to cancel your reservation
                                </a>
                            </p>
                            <p style="color: #5C4033; font-size: 14px; line-height: 1.6; font-family: Georgia,
                             serif; margin: 20px 0 0 0;">
                                If you need to cancel or change your reservation you can either
                                click the cancel button over or contact us directly.
                            </p>
                        </td>
                    </tr>

                    <!-- Footer -->
                    <tr>
                        <td bgcolor="#2C2416" align="center" style="padding: 20px; border-radius: 0 0 12px 12px;">
                            <p style="color: #D4AF37; margin: 0; font-size: 13px; letter-spacing: 1px;
                             font-family: Georgia, serif;">
                                © 2026 Restaurant Name. All rights reserved.
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>'''
            msg = EmailMessage(
                subject='Reservation Confirmation',
                body=html_body,
                from_email=None,
                to=[email]
            )
            msg.content_subtype = 'html'
            msg.send()
        except Exception as e:
            print(f"Reservation Email Error: {e}")

        return render_template("reservation_success.html", name=name, email=email,
                               date=resv_date, time=resv_time, guests=guests, table=table)

    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM restaurant_customer_tables WHERE is_active = TRUE ORDER BY table_number ASC")
    tables = cursor.fetchall()
    cursor.close()
    db.close()
    today = date.today().isoformat()
    return render_template("reservations.html", today=today, tables=tables)

def my_reservations():
    if 'customer_id' not in session:
        return redirect(url_for('customer_auth.customer_login'))

    customer_id = session['customer_id']

    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT * FROM reservations_restaurant
        WHERE customer_email = (
            SELECT email FROM customer_accounts WHERE customer_id = %s
        )
        ORDER BY reservation_date DESC, reservation_time DESC
    """, (customer_id,))
    reservations = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template("customer/my_reservations.html", reservations=reservations)

def cancel_reservation(resv_id):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("""SELECT table_number FROM reservations_restaurant WHERE reservation_id = %s""", (resv_id,))
    reservation = cursor.fetchone()

    if not reservation:
        cursor.close()
        db.close()
        flash("Reservation not found", "danger")
        return redirect(url_for('general.home'))

    table_num = reservation["table_number"]

    cursor.execute("""
        UPDATE reservations_restaurant
        SET reservation_status = 'Cancelled'
        WHERE reservation_id = %s
    """, (resv_id,))
    db.commit()

    cursor.close()
    db.close()
    socketio.emit('table_available', {
        'table_num': table_num
    }, broadcast=True)

    return render_template("reservation_cancelled.html", table=table_num)
