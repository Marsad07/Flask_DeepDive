from flask import render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required
from app2.database import get_db, staff_redirect
from app2 import mail, login_manager
from app2.models.customer_user import CustomerUser
from flask_mailman import EmailMessage
import secrets
from datetime import datetime, timedelta

@staff_redirect
def customer_login():
    if request.method == "POST":
        customer_email = request.form['customer_email']
        customer_password = request.form['customer_password']

        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM customer_accounts WHERE customer_email = %s", (customer_email,))
        user = cursor.fetchone()
        cursor.close()
        db.close()

        if user and check_password_hash(user['customer_password_hash'], customer_password):
            # Log in with Flask-Login
            customer_user = CustomerUser(user)
            login_user(customer_user)

            # Keep session data for your existing session-based checks
            session['customer_id'] = user['customer_id']
            session['customer_name'] = user['customer_fullname']
            session['customer_email'] = user['customer_email']
            session['customer_phonenum'] = user['customer_phonenum']
            return redirect(url_for('customer_auth.customer_dashboard'))
        else:
            return render_template('auth/login.html', error="Incorrect email or password")

    return render_template('auth/login.html')

@staff_redirect
def customer_register():
    if request.method == "POST":
        customer_fullname = request.form['customer_fullname']
        customer_email = request.form['customer_email']
        customer_phonenum = request.form['customer_phonenum']
        customer_password = request.form['customer_password']

        db = get_db()
        cursor = db.cursor(dictionary=True)

        cursor.execute("SELECT * FROM customer_accounts WHERE customer_email = %s", (customer_email,))
        user = cursor.fetchone()

        if user:
            cursor.close()
            db.close()
            return render_template('auth/register.html',
                                   error="An account with this email already exists")

        hashed_password = generate_password_hash(customer_password)

        cursor.execute("""
            INSERT INTO customer_accounts (customer_fullname, customer_email, customer_phonenum, customer_password_hash)
            VALUES (%s, %s, %s, %s)
        """, (customer_fullname, customer_email, customer_phonenum, hashed_password))
        db.commit()

        new_id = cursor.lastrowid

        # Log in with Flask-Login
        new_user_row = {
            "customer_id": new_id,
            "customer_fullname": customer_fullname,
            "customer_email": customer_email
        }
        login_user(CustomerUser(new_user_row))

        session['customer_id'] = new_id
        session['customer_name'] = customer_fullname
        session['customer_email'] = customer_email

        cursor.close()
        db.close()
        return redirect(url_for('customer_auth.customer_dashboard'))

    return render_template('auth/register.html')

def customer_logout():
    logout_user()
    session.clear()
    return redirect(url_for('general.home_page'))

@staff_redirect
def customer_dashboard():
    if 'customer_id' not in session:
        return redirect(url_for('customer_auth.login'))

    customer_id = session['customer_id']
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT * FROM customer_accounts WHERE customer_id = %s", (customer_id,))
    customer = cursor.fetchone()

    cursor.execute("SELECT COUNT(*) as count FROM customer_orders WHERE customer_id = %s", (customer_id,))
    total_orders = cursor.fetchone()['count']

    cursor.execute("SELECT SUM(total_price) as total FROM customer_orders WHERE customer_id = %s", (customer_id,))
    total_spent = cursor.fetchone()['total'] or 0

    cursor.execute("""
        SELECT item_name, COUNT(*) as count 
        FROM order_items 
        WHERE order_id IN (SELECT order_id FROM customer_orders WHERE customer_id = %s)
        GROUP BY item_name 
        ORDER BY count DESC 
        LIMIT 1
    """, (customer_id,))
    fav = cursor.fetchone()
    customer_fav_item = fav['item_name'] if fav else 'None'

    cursor.execute("""
        SELECT * FROM customer_orders 
        WHERE customer_id = %s 
        ORDER BY order_date DESC, order_time DESC 
        LIMIT 5
    """, (customer_id,))
    recent_orders = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template('auth/customer_dashboard.html',
                           customer_fullname=customer['customer_fullname'],
                           total_orders=total_orders,
                           total_spent=f"£{total_spent:.2f}",
                           customer_fav_item=customer_fav_item,
                           recent_orders=recent_orders)

@staff_redirect
def customer_order_history():
    if 'customer_id' not in session:
        return redirect(url_for('customer_auth.login'))

    customer_id = session['customer_id']
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT * FROM customer_orders
        WHERE customer_id = %s
        ORDER BY order_date DESC, order_time DESC
    """, (customer_id,))
    orders = cursor.fetchall()
    cursor.close()
    db.close()

    return render_template('auth/customer_order_history.html', orders=orders)

def customer_profile_settings():
    if 'customer_id' not in session:
        return redirect(url_for('customer_auth.login'))

    customer_id = session['customer_id']
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT * FROM customer_accounts WHERE customer_id = %s", (customer_id,))
    customer = cursor.fetchone()
    cursor.close()
    db.close()

    return render_template('auth/customer_profile.html', customer=customer)

@staff_redirect
def update_profile():
    if 'customer_id' not in session:
        return redirect(url_for('customer_auth.login'))

    customer_id = session['customer_id']
    db = get_db()
    cursor = db.cursor(dictionary=True)

    if request.method == "POST":
        fullname = request.form.get('customer_fullname')
        email = request.form.get('customer_email')
        phone = request.form.get('customer_phonenum')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        cursor.execute("""
            UPDATE customer_accounts 
            SET customer_fullname = %s, customer_email = %s, customer_phonenum = %s
            WHERE customer_id = %s
        """, (fullname, email, phone, customer_id))

        if new_password:
            if new_password == confirm_password:
                hashed = generate_password_hash(new_password)
                cursor.execute("""
                    UPDATE customer_accounts 
                    SET customer_password_hash = %s 
                    WHERE customer_id = %s
                """, (hashed, customer_id))
            else:
                cursor.execute("SELECT * FROM customer_accounts WHERE customer_id = %s", (customer_id,))
                customer = cursor.fetchone()
                cursor.close()
                db.close()
                return render_template('auth/customer_profile.html',
                                       customer=customer,
                                       error="Passwords do not match!")

        db.commit()
        session['customer_name'] = fullname
        session['customer_email'] = email
        cursor.execute("SELECT * FROM customer_accounts WHERE customer_id = %s", (customer_id,))
        customer = cursor.fetchone()
        cursor.close()
        db.close()
        return render_template('auth/customer_profile.html',
                               customer=customer, success="Profile updated successfully!")

    cursor.close()
    db.close()
    return redirect(url_for('customer_auth.customer_profile_settings'))

@staff_redirect
def order_history():
    customer_id = session.get('customer_id')
    if not customer_id:
        return redirect(url_for('customer_auth.login'))  # FIXED: was 'auth.login_page'

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT 
            order_id,
            CONCAT('ORD-', DATE_FORMAT(created_at, '%Y%m%d'), '-', 
                LPAD((SELECT COUNT(*) FROM customer_orders co2 
                      WHERE DATE(co2.created_at) = DATE(customer_orders.created_at) 
                      AND co2.order_id <= customer_orders.order_id), 3, '0')
            ) AS order_number,
            order_type,
            total_price,
            order_status,
            payment_status,
            created_at
        FROM customer_orders
        WHERE customer_id = %s
        ORDER BY created_at DESC
    """, (customer_id,))

    orders = cursor.fetchall()
    cursor.close()
    db.close()
    return render_template("auth/order_history.html", orders=orders)


@staff_redirect
def forgot_password():
    if request.method == "POST":
        email = request.form.get('email')

        db = get_db()
        cursor = db.cursor(dictionary=True)

        cursor.execute("SELECT * FROM customer_accounts WHERE customer_email = %s", (email,))
        customer = cursor.fetchone()

        if customer:
            token = secrets.token_urlsafe(32)
            expires_at = datetime.now() + timedelta(hours=1)

            cursor.execute("""
                INSERT INTO password_resets (customer_email, token, expires_at)
                VALUES (%s, %s, %s)
            """, (email, token, expires_at))
            db.commit()

            reset_url = url_for('customer_auth.reset_password', token=token, _external=True)
            try:
                html_body = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body bgcolor="#F8F4EC" style="margin: 0; padding: 0;">
    <table width="100%" bgcolor="#F8F4EC" cellpadding="0" cellspacing="0" border="0">
        <tr>
            <td align="center" style="padding: 40px 20px;">
                <table width="600" cellpadding="0" cellspacing="0" border="0" style="max-width: 600px; width: 100%;">
                    <tr>
                        <td bgcolor="#2C2416" align="center" style="padding: 30px; border-radius: 12px 12px 0 0;">
                            <h1 style="color: #FFD700; margin: 0; font-size: 28px;
                            letter-spacing: 3px; font-family: Georgia, serif;">
                                RESTAURANT NAME
                            </h1>
                            <p style="color: #D4AF37; margin: 8px 0 0 0; font-size: 14px; letter-spacing: 2px;
                             font-family: Georgia, serif;">
                                PASSWORD RESET
                            </p>
                        </td>
                    </tr>
                    <tr>
                        <td bgcolor="#FFFFFF" style="padding: 30px;">
                            <p style="color: #2C2416; font-size: 16px; font-family: Georgia, serif; margin: 0 0 10px 0;">
                                Hi {customer['customer_fullname']},
                            </p>
                            <p style="color: #5C4033; font-size: 15px; line-height: 1.6; font-family: Georgia, serif;
                             margin: 0 0 20px 0;">
                                We received a request to reset your password. Click the button below to set a new one. 
                                This link will expire in 1 hour.
                            </p>
                            <table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin: 30px 0;">
                                <tr>
                                    <td align="center">
                                        <a href="{reset_url}" style="background-color: #8B0000; color: #FFD700;
                                         padding: 14px 35px; text-decoration: none; border-radius: 8px;
                                          font-size: 15px; font-weight: bold; letter-spacing: 2px;
                                           text-transform: uppercase; font-family: Georgia, serif;
                                            display: inline-block;">
                                            RESET PASSWORD
                                        </a>
                                    </td>
                                </tr>
                            </table>
                            <p style="color: #5C4033; font-size: 13px; line-height: 1.6; font-family: Georgia,
                             serif; margin: 0;">
                                If you didn't request a password reset you can safely ignore this email.
                            </p>
                        </td>
                    </tr>
                    <tr>
                        <td bgcolor="#2C2416" align="center" style="padding: 20px; border-radius: 0 0 12px 12px;">
                            <p style="color: #D4AF37; margin: 0;
                             font-size: 13px; letter-spacing: 1px; font-family: Georgia, serif;">
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
                    subject='Password Reset Request',
                    body=html_body,
                    from_email=None,
                    to=[email]
                )
                msg.content_subtype = 'html'
                msg.send()
            except Exception as e:
                print(f"Reset email error: {e}")

        cursor.close()
        db.close()
        return render_template('auth/forgot_password.html', reset_sent=True)

    return render_template('auth/forgot_password.html', reset_sent=False)

@staff_redirect
def reset_password(token):
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT * FROM password_resets 
        WHERE token = %s AND used = 0 AND expires_at > NOW()
    """, (token,))
    reset = cursor.fetchone()

    if not reset:
        cursor.close()
        db.close()
        return render_template('auth/reset_password.html',
                               error="This reset link is invalid or has expired.")

    if request.method == "POST":
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        if new_password != confirm_password:
            cursor.close()
            db.close()
            return render_template('auth/reset_password.html',
                                   token=token,
                                   error="Passwords do not match.")

        hashed = generate_password_hash(new_password)
        cursor.execute("""
            UPDATE customer_accounts SET customer_password_hash = %s 
            WHERE customer_email = %s
        """, (hashed, reset['customer_email']))

        cursor.execute("UPDATE password_resets SET used = 1 WHERE token = %s", (token,))
        db.commit()
        cursor.close()
        db.close()

        return redirect(url_for('customer_auth.login') + '?reset=success')

    cursor.close()
    db.close()
    return render_template('auth/reset_password.html', token=token)