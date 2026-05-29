from flask import render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash
from flask_login import login_user, logout_user
from app2.database import get_db, staff_redirect
from app2 import mail
from app2.models.customer_user import CustomerUser
from app2.schemas import RegisterSchema, UpdateProfileSchema
from flask_mailman import EmailMessage
from marshmallow import ValidationError
import secrets
from datetime import datetime, timedelta

@staff_redirect
def customer_login():
    if request.method == "POST":
        email    = request.form['customer_email']
        password = request.form['customer_password']

        # Use model method instead of raw SQL
        user = CustomerUser.get_by_email(email)

        if user and user.check_password(password):
            login_user(user)

            # Keep session data for existing session-based checks
            session['customer_id']    = user.customer_id
            session['customer_name']  = user.customer_fullname
            session['customer_email'] = user.customer_email
            return redirect(url_for('customer_auth.customer_dashboard'))

        return render_template('auth/login.html', error="Incorrect email or password")

    return render_template('auth/login.html')

@staff_redirect
def customer_register():
    if request.method == "POST":
        # Validates registration form data using Marshmallow
        schema = RegisterSchema()
        try:
            validated = schema.load(request.form)
        except ValidationError as err:
            first_error = next(iter(err.messages.values()))[0]
            return render_template('auth/register.html', error=first_error)

        fullname = validated['customer_fullname']
        email    = validated['customer_email']
        phone    = validated['customer_phonenum']
        password = validated['customer_password']

        # Check if email already exists using model method
        existing = CustomerUser.get_by_email(email)
        if existing:
            return render_template('auth/register.html',
                                   error="An account with this email already exists")

        # I use raw SQL here to include phone number since model doesn't have it as a column yet
        # TODO: add customer_phonenum to CustomerUser model
        db = get_db()
        cursor = db.cursor(dictionary=True)
        hashed = generate_password_hash(password)
        cursor.execute("""
            INSERT INTO customer_accounts 
            (customer_fullname, customer_email, customer_phonenum, customer_password_hash)
            VALUES (%s, %s, %s, %s)
        """, (fullname, email, phone, hashed))
        db.commit()
        new_id = cursor.lastrowid
        cursor.close()
        db.close()

        # Fetch the new user via model and log them in
        new_user = CustomerUser.get_by_id(new_id)
        login_user(new_user)

        session['customer_id']    = new_id
        session['customer_name']  = fullname
        session['customer_email'] = email
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

    cursor.execute("SELECT COUNT(*) as count FROM customer_orders WHERE customer_id = %s",
                   (customer_id,))
    total_orders = cursor.fetchone()['count']

    cursor.execute("SELECT SUM(total_price) as total FROM customer_orders WHERE customer_id = %s",
                   (customer_id,))
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
        # Validate profile update form data using Marshmallow
        schema = UpdateProfileSchema()
        try:
            validated = schema.load(request.form)
        except ValidationError as err:
            first_error = next(iter(err.messages.values()))[0]
            cursor.execute("SELECT * FROM customer_accounts WHERE customer_id = %s",
                           (customer_id,))
            customer = cursor.fetchone()
            cursor.close()
            db.close()
            return render_template('auth/customer_profile.html',
                                   customer=customer, error=first_error)

        fullname     = validated['customer_fullname']
        email        = validated['customer_email']
        phone        = validated['customer_phonenum']
        new_password = validated.get('new_password')
        confirm      = request.form.get('confirm_password')

        cursor.execute("""
            UPDATE customer_accounts 
            SET customer_fullname = %s, customer_email = %s, customer_phonenum = %s
            WHERE customer_id = %s
        """, (fullname, email, phone, customer_id))

        if new_password:
            if new_password == confirm:
                hashed = generate_password_hash(new_password)
                cursor.execute("""
                    UPDATE customer_accounts 
                    SET customer_password_hash = %s 
                    WHERE customer_id = %s
                """, (hashed, customer_id))
            else:
                cursor.execute("SELECT * FROM customer_accounts WHERE customer_id = %s",
                               (customer_id,))
                customer = cursor.fetchone()
                cursor.close()
                db.close()
                return render_template('auth/customer_profile.html',
                                       customer=customer,
                                       error="Passwords do not match!")

        db.commit()
        session['customer_name']  = fullname
        session['customer_email'] = email

        cursor.execute("SELECT * FROM customer_accounts WHERE customer_id = %s", (customer_id,))
        customer = cursor.fetchone()
        cursor.close()
        db.close()
        return render_template('auth/customer_profile.html',
                               customer=customer,
                               success="Profile updated successfully!")

    cursor.close()
    db.close()
    return redirect(url_for('customer_auth.customer_profile_settings'))

@staff_redirect
def order_history():
    customer_id = session.get('customer_id')
    if not customer_id:
        return redirect(url_for('customer_auth.login'))

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
        email  = request.form.get('email')
        db     = get_db()
        cursor = db.cursor(dictionary=True)

        cursor.execute("SELECT * FROM customer_accounts WHERE customer_email = %s", (email,))
        customer = cursor.fetchone()

        if customer:
            token      = secrets.token_urlsafe(32)
            expires_at = datetime.now() + timedelta(hours=1)

            cursor.execute("""
                INSERT INTO password_resets (customer_email, token, expires_at)
                VALUES (%s, %s, %s)
            """, (email, token, expires_at))
            db.commit()

            reset_url = url_for('customer_auth.reset_password', token=token, _external=True)
            try:
                # Send password reset email — HTML rendered from template, not built inline
                html_body = render_template(
                    'emails/password_reset_email.html',
                    customer_fullname=customer['customer_fullname'],
                    reset_url=reset_url
                )
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
        confirm      = request.form.get('confirm_password')

        if new_password != confirm:
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