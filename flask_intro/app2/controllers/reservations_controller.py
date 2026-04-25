from flask import render_template, request, redirect, url_for, flash, session
from app2.database import get_db, staff_redirect
from datetime import date, datetime
from app2 import socketio
from flask_mailman import EmailMessage

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
            cursor2.execute(
                "SELECT * FROM restaurant_customer_tables "
                "WHERE is_active = TRUE ORDER BY table_number ASC"
            )
            tables = cursor2.fetchall()
            cursor2.close()
            today = date.today().isoformat()
            return render_template(
                "reservations.html",
                today=today,
                tables=tables,
                error="Sorry, this table is already booked for that time. Please select another table."
            )

        cursor.execute("""
            INSERT INTO reservations_restaurant 
            (customer_fullname, customer_email, customer_phonenum, reservation_date, 
             reservation_time, num_of_guests, table_number, special_requests) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (name, email, phone, resv_date, resv_time, guests, table, special_requests))
        db.commit()
        reservation_id = cursor.lastrowid

        cursor.close()
        db.close()

        socketio.emit('table_unavailable', {'table_num': table})

        try:
            cancel_url = url_for(
                'reservations.cancel_page',
                resv_id=reservation_id,
                _external=True
            )

            view_url = url_for(
                'reservations.guest_find_reservation',
                _external=True
            )
            html_template = f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
              <meta charset="UTF-8">
              <meta name="viewport" content="width=device-width, initial-scale=1.0">
              <title>Reservation Confirmation</title>
            </head>
            <body style="margin:0; padding:0; background:#F5F0E8; font-family:Georgia, serif;">
              <table width="100%" cellpadding="0" cellspacing="0" border="0"
                     style="background:#F5F0E8; padding:40px 20px;">
                <tr>
                  <td align="center">
                    <table width="100%" cellpadding="0" cellspacing="0" border="0"
                           style="max-width:560px; background:#ffffff;
                                  border-radius:2px;
                                  box-shadow:0 2px 24px rgba(139,0,0,0.08);">
                      <tr>
                        <td style="background:linear-gradient(90deg,#8B0000,#D4AF37,#8B0000);
                                   height:4px; border-radius:2px 2px 0 0; font-size:0;">
                          &nbsp;
                        </td>
                      </tr>
                      <tr>
                        <td align="center"
                            style="background:#8B0000; padding:36px 40px 30px;">
                          <p style="margin:0 0 10px; font-family:Georgia,serif;
                                    font-size:11px; letter-spacing:3px;
                                    text-transform:uppercase; color:#D4AF37;">
                            Reservation Confirmed
                          </p>
                          <h1 style="margin:0; font-family:Georgia,serif;
                                     font-size:28px; font-weight:700;
                                     color:#ffffff; line-height:1.2;">
                            Your Table is Booked
                          </h1>
                          <p style="margin:12px 0 0; font-family:Arial,sans-serif;
                                    font-size:14px; color:rgba(255,255,255,0.65);
                                    letter-spacing:0.3px;">
                            We look forward to seeing you
                          </p>
                        </td>
                      </tr>
                      <tr>
                        <td style="padding:36px 44px 0;">
                          <p style="margin:0; font-family:Arial,sans-serif;
                                    font-size:15px; color:#4A3728; line-height:1.6;">
                            Hi <strong style="color:#1C1008;">{name}</strong>,
                          </p>
                          <p style="margin:10px 0 0; font-family:Arial,sans-serif;
                                    font-size:15px; color:#4A3728; line-height:1.6;">
                            Your reservation has been confirmed. Here's a summary of your booking:
                          </p>
                        </td>
                      </tr>
                      <tr>
                        <td style="padding:28px 44px 0;">
                          <table width="100%" cellpadding="0" cellspacing="0" border="0"
                                 style="border:1px solid #EDE4D3; border-radius:2px;
                                        overflow:hidden;">
                            <tr>
                              <td width="50%"
                                  style="padding:18px 22px; border-bottom:1px solid #EDE4D3;
                                         border-right:1px solid #EDE4D3;">
                                <p style="margin:0 0 4px; font-family:Arial,sans-serif;
                                           font-size:10px; font-weight:700; letter-spacing:2px;
                                           text-transform:uppercase; color:#8B0000;">
                                  Date
                                </p>
                                <p style="margin:0; font-family:Georgia,serif;
                                           font-size:18px; font-weight:600; color:#1C1008;">
                                  {resv_date}
                                </p>
                              </td>
                              <td width="50%"
                                  style="padding:18px 22px; border-bottom:1px solid #EDE4D3;">
                                <p style="margin:0 0 4px; font-family:Arial,sans-serif;
                                           font-size:10px; font-weight:700; letter-spacing:2px;
                                           text-transform:uppercase; color:#8B0000;">
                                  Time
                                </p>
                                <p style="margin:0; font-family:Georgia,serif;
                                           font-size:18px; font-weight:600; color:#1C1008;">
                                  {resv_time}
                                </p>
                              </td>
                            </tr>
                            <tr>
                              <td width="50%"
                                  style="padding:18px 22px;
                                         border-right:1px solid #EDE4D3;">
                                <p style="margin:0 0 4px; font-family:Arial,sans-serif;
                                           font-size:10px; font-weight:700; letter-spacing:2px;
                                           text-transform:uppercase; color:#8B0000;">
                                  Guests
                                </p>
                                <p style="margin:0; font-family:Georgia,serif;
                                           font-size:18px; font-weight:600; color:#1C1008;">
                                  {guests}
                                </p>
                              </td>
                              <td width="50%"
                                  style="padding:18px 22px;">
                                <p style="margin:0 0 4px; font-family:Arial,sans-serif;
                                           font-size:10px; font-weight:700; letter-spacing:2px;
                                           text-transform:uppercase; color:#8B0000;">
                                  Table
                                </p>
                                <p style="margin:0; font-family:Georgia,serif;
                                           font-size:18px; font-weight:600; color:#1C1008;">
                                  {table}
                                </p>
                              </td>
                            </tr>
                          </table>
                        </td>
                      </tr>
                      <tr>
                        <td style="padding:32px 44px 0;">
                          <table width="100%" cellpadding="0" cellspacing="0" border="0">
                            <tr>
                              <!-- View / Modify -->
                              <td width="48%" align="center">
                                <a href="{view_url}"
                                   style="display:block; background:#8B0000; color:#D4AF37;
                                          font-family:Arial,sans-serif; font-size:12px;
                                          font-weight:700; letter-spacing:1.5px;
                                          text-transform:uppercase; text-decoration:none;
                                          padding:14px 10px; border-radius:2px;
                                          box-shadow:0 3px 12px rgba(139,0,0,0.25);">
                                  View / Modify
                                </a>
                              </td>
                              <td width="4%"></td>
                              <!-- Cancel -->
                              <td width="48%" align="center">
                                <a href="{cancel_url}"
                                   style="display:block; background:#ffffff; color:#8B0000;
                                          font-family:Arial,sans-serif; font-size:12px;
                                          font-weight:700; letter-spacing:1.5px;
                                          text-transform:uppercase; text-decoration:none;
                                          padding:13px 10px; border-radius:2px;
                                          border:1.5px solid #D4AF37;">
                                  Cancel Reservation
                                </a>
                              </td>
                            </tr>
                          </table>
                        </td>
                      </tr>
                      <tr>
                        <td style="padding:36px 44px 0;">
                          <div style="height:1px; background:linear-gradient(
                                      90deg,#D4AF37 0%,transparent 100%);
                                      opacity:0.4;">
                          </div>
                        </td>
                      </tr>
                      <tr>
                        <td style="padding:24px 44px 40px;">
                          <p style="margin:0; font-family:Arial,sans-serif;
                                    font-size:12px; color:#9E8C78; line-height:1.7;">
                            This email was sent to confirm your reservation.
                            If you did not make this booking, you can safely ignore this email
                            or <a href="{cancel_url}"
                                  style="color:#8B0000; text-decoration:underline;">
                              cancel it here</a>.
                          </p>
                        </td>
                      </tr>
                      <tr>
                        <td style="background:linear-gradient(90deg,#8B0000,#D4AF37,#8B0000);
                                   height:3px; border-radius:0 0 2px 2px; font-size:0;">
                          &nbsp;
                        </td>
                      </tr>
                    </table>
                  </td>
                </tr>
              </table>
            </body>
            </html>
            """
            msg = EmailMessage(
                subject='Reservation Confirmation',
                body=html_template,
                from_email="noreply@restaurant.com",
                to=[email]
            )
            msg.content_subtype = 'html'
            msg.send()

        except Exception:
            import traceback
            print("Reservation Email Error:")
            traceback.print_exc()

        return render_template(
            "reservation_success.html",
            name=name,
            email=email,
            date=resv_date,
            time=resv_time,
            guests=guests,
            table=table
        )

    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        "SELECT * FROM restaurant_customer_tables "
        "WHERE is_active = TRUE ORDER BY table_number ASC"
    )
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
    return render_template("auth/my_reservations.html", reservations=reservations)

def cancel_reservation(resv_id):
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT * FROM reservations_restaurant WHERE customer_id = %s", (resv_id,))
    r = cursor.fetchone()

    if not r:
        cursor.close()
        db.close()
        return render_template("auth/error_cancel.html", message="Reservation not found.")

    if r["reservation_status"] == "Cancelled":
        cursor.close()
        db.close()
        return render_template("auth/already_cancelled.html", r=r)

    cursor.execute("""
        UPDATE reservations_restaurant
        SET reservation_status = 'Cancelled'
        WHERE customer_id = %s
    """, (resv_id,))
    db.commit()
    email_html = f"""
       <!DOCTYPE html>
       <html>
       <body style="font-family: Georgia, serif; background: #FFFEF2; padding: 20px;">
         <div style="max-width: 600px; margin: auto; background: white; padding: 30px; border-radius: 8px;
                     border: 1px solid #D4AF37;">
           <h2 style="color: #8B0000; text-align: center;">Reservation Cancelled</h2>

           <p style="font-size: 16px; color: #2C2416;">
             Hello <strong>{r['customer_fullname']}</strong>,
           </p>

           <p style="font-size: 16px; color: #2C2416;">
             Your reservation has been successfully cancelled.
           </p>

           <div style="margin-top: 20px; padding: 15px; background: #FFF8E6; border-left: 4px solid #8B0000;">
             <p style="margin: 0; font-size: 15px;">
               <strong>Date:</strong> {r['reservation_date']}<br>
               <strong>Time:</strong> {r['reservation_time']}<br>
               <strong>Guests:</strong> {r['num_of_guests']}<br>
               <strong>Table:</strong> {r['table_number']}
             </p>
           </div>

           <p style="margin-top: 30px; font-size: 15px; color: #5C4033;">
             If this was a mistake, you can make a new reservation anytime.
           </p>

           <p style="margin-top: 20px; font-size: 14px; color: #8B0000; text-align: center;">
             Thank you for choosing our restaurant.
           </p>
         </div>
       </body>
       </html>
       """

    msg = EmailMessage(
        subject="Your Reservation Has Been Cancelled",
        body=email_html,
        from_email="noreply@restaurant.com",
        to=[r["customer_email"]],
    )
    msg.content_subtype = "html"

    try:
        msg.send()
    except Exception as e:
        print("Email send error:", repr(e))

    cursor.close()
    db.close()
    return render_template("auth/reservation_cancelled.html", r=r)

def modify_reservation(resv_id):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        "SELECT * FROM reservations_restaurant WHERE customer_id = %s",
        (resv_id,)
    )
    old = cursor.fetchone()

    if not old:
        cursor.close()
        db.close()
        flash("Reservation not found.", "danger")
        return redirect(url_for("reservations.my_reservations"))

    if request.method == "GET":
        cursor.close()
        db.close()
        return render_template("auth/modify_reservation.html", r=old)

    new_date = request.form.get("date")
    new_time = request.form.get("time")
    new_table = int(request.form.get("table"))
    new_guests = int(request.form.get("guests"))

    new_dt = datetime.strptime(f"{new_date} {new_time}", "%Y-%m-%d %H:%M")
    if new_dt < datetime.now():
        cursor.close()
        db.close()
        flash("You cannot choose a past date or time.", "danger")
        return redirect(url_for("reservations.modify_reservation", resv_id=resv_id))

    cursor.execute(
        "SELECT capacity FROM restaurant_customer_tables WHERE table_number = %s",
        (new_table,)
    )
    table_info = cursor.fetchone()

    if not table_info:
        cursor.close()
        db.close()
        flash("Invalid table number.", "danger")
        return redirect(url_for("reservations.modify_reservation", resv_id=resv_id))

    if new_guests > table_info["capacity"]:
        cursor.close()
        db.close()
        flash("Too many guests for this table.", "danger")
        return redirect(url_for("reservations.modify_reservation", resv_id=resv_id))

    cursor.execute("""
        SELECT * FROM reservations_restaurant
        WHERE table_number = %s
          AND reservation_date = %s
          AND reservation_time = %s
          AND customer_id != %s
          AND reservation_status != 'Cancelled'
    """, (new_table, new_date, new_time, resv_id))

    conflict = cursor.fetchone()

    if conflict:
        cursor.close()
        db.close()
        flash("This table is already booked at that time.", "danger")
        return redirect(url_for("reservations.modify_reservation", resv_id=resv_id))

    cursor.execute("""
        UPDATE reservations_restaurant
        SET reservation_date = %s,
            reservation_time = %s,
            table_number = %s,
            num_of_guests = %s
        WHERE customer_id = %s
    """, (new_date, new_time, new_table, new_guests, resv_id))
    db.commit()
    cursor.close()
    db.close()

    subject = "Your Reservation Has Been Updated"
    body = f"""
    Hello,
    Your reservation has been successfully updated.
    New Details:
    - Date: {new_date}
    - Time: {new_time}
    - Table: {new_table}
    - Guests: {new_guests}
    Thank you for choosing our restaurant!
    """
    email_msg = EmailMessage(subject, body, to=[old["customer_email"]])
    email_msg.send()
    flash("Reservation updated successfully!", "success")
    return redirect(url_for("reservations.my_reservations"))

def cancel_page(resv_id):
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT * FROM reservations_restaurant WHERE customer_id = %s", (resv_id,))
    reservation = cursor.fetchone()

    cursor.close()
    db.close()

    if not reservation:
        flash("Reservation not found", "danger")
        return redirect(url_for('general.home_page'))

    return render_template("auth/cancel_confirm.html", r=reservation)

def guest_find_reservation():
    if request.method == "GET":
        return render_template("auth/guest_find.html")

    email = request.form.get("email")
    phone = request.form.get("phone")

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT * FROM reservations_restaurant
        WHERE customer_email = %s AND customer_phonenum = %s
        ORDER BY reservation_date DESC, reservation_time DESC
    """, (email, phone))

    results = cursor.fetchall()

    cursor.close()
    db.close()

    if not results:
        flash("No reservation found with those details.", "danger")
        return redirect(url_for("reservations.guest_find_reservation"))
    reservation = results[0]
    return redirect(url_for("reservations.guest_view_reservation", resv_id=reservation["customer_id"]))

def guest_view_reservation(resv_id):
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT * FROM reservations_restaurant WHERE customer_id = %s", (resv_id,))
    reservation = cursor.fetchone()

    cursor.close()
    db.close()

    if not reservation:
        flash("Reservation not found.", "danger")
        return redirect(url_for("reservations.guest_find_reservation"))

    return render_template("auth/guest_view.html", r=reservation)

def guest_modify_reservation(resv_id):
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT * FROM reservations_restaurant WHERE customer_id = %s", (resv_id,))
    r = cursor.fetchone()

    if not r:
        cursor.close()
        db.close()
        flash("Reservation not found.", "danger")
        return redirect(url_for("reservations.guest_find_reservation"))

    if request.method == "POST":
        new_date = request.form.get("date")
        new_time = request.form.get("time")
        new_table = request.form.get("table")
        new_guests = request.form.get("guests")

        cursor.execute("""
            UPDATE reservations_restaurant
            SET reservation_date=%s, reservation_time=%s, table_number=%s, num_of_guests=%s
            WHERE customer_id=%s
        """, (new_date, new_time, new_table, new_guests, resv_id))

        db.commit()
        cursor.close()
        db.close()

        return redirect(url_for("reservations.guest_view_reservation", resv_id=resv_id))

    cursor.close()
    db.close()
    return render_template("auth/guest_modify_reservation.html", r=r)


