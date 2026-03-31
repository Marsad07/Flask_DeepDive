from flask import render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from app2.database import get_db

def customer_login():
    if request.method == "POST":
        customer_email = request.form['customer_email']
        customer_password = request.form['customer_password']

        # This checks for the user's credentials
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM customer_accounts WHERE customer_email = %s", (customer_email,))
        user = cursor.fetchone()
        cursor.close()
        db.close()

        # This verifies the password
        if user and check_password_hash(user['customer_password_hash'], customer_password):
            # Successful login - set session
            session['customer_id'] = user['customer_id']
            session['customer_name'] = user['customer_fullname']
            session['customer_email'] = user['customer_email']
            return redirect(url_for('customer_auth.customer_dashboard'))
        else:
            # Login failed
            return render_template('auth/login.html', error="Incorrect email or password")

    return render_template('auth/login.html')

def customer_register():
    if request.method == "POST":
        customer_fullname = request.form['customer_fullname']
        customer_email = request.form['customer_email']
        customer_phonenum = request.form['customer_phonenum']
        customer_password = request.form['customer_password']

        db = get_db()
        cursor = db.cursor(dictionary=True)

        # Check if email already exists
        cursor.execute("SELECT * FROM customer_accounts WHERE customer_email = %s", (customer_email,))
        user = cursor.fetchone()

        if user:
            cursor.close()
            db.close()
            return render_template('auth/register.html',
                                   error="An account with this email already exists")

        # Hashes the password
        hashed_password = generate_password_hash(customer_password)

        # Inserts new user
        cursor.execute("""
            INSERT INTO customer_accounts (customer_fullname, customer_email, customer_phonenum, customer_password_hash)
            VALUES (%s, %s, %s, %s)
        """, (customer_fullname, customer_email, customer_phonenum, hashed_password))
        db.commit()

        # Auto-login after registration
        session['customer_id'] = cursor.lastrowid
        session['customer_name'] = customer_fullname
        session['customer_email'] = customer_email

        cursor.close()
        db.close()
        return redirect(url_for('customer_auth.customer_dashboard'))

    return render_template('auth/register.html')

def customer_logout():
    session.clear()
    return redirect(url_for('general.home_page'))

def customer_dashboard():
    # Check if logged in
    if 'customer_id' not in session:
        return redirect(url_for('customer_auth.login'))

    customer_id = session['customer_id']
    db = get_db()
    cursor = db.cursor(dictionary=True)

    # Get customer info
    cursor.execute("SELECT * FROM customer_accounts WHERE customer_id = %s", (customer_id,))
    customer = cursor.fetchone()

    # Get total orders
    cursor.execute("SELECT COUNT(*) as count FROM customer_orders WHERE customer_id = %s", (customer_id,))
    total_orders = cursor.fetchone()['count']

    # Get total spent
    cursor.execute("SELECT SUM(total_price) as total FROM customer_orders WHERE customer_id = %s", (customer_id,))
    total_spent = cursor.fetchone()['total'] or 0

    # Get favorite item (most ordered)
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

    # Get recent orders (last 5)
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

def update_profile():
    # This checks if logged in
    if 'customer_id' not in session:
        return redirect(url_for('customer_auth.login'))

    customer_id = session['customer_id']
    db = get_db()
    cursor = db.cursor(dictionary=True)

    if request.method == "POST":
        # Gets form data
        fullname = request.form.get('customer_fullname')
        email = request.form.get('customer_email')
        phone = request.form.get('customer_phonenum')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        # Updates basic info
        cursor.execute("""
            UPDATE customer_accounts 
            SET customer_fullname = %s, customer_email = %s, customer_phonenum = %s
            WHERE customer_id = %s
        """, (fullname, email, phone, customer_id))

        # Updates password if provided
        if new_password:
            if new_password == confirm_password:
                hashed = generate_password_hash(new_password)
                cursor.execute("""
                    UPDATE customer_accounts 
                    SET customer_password_hash = %s 
                    WHERE customer_id = %s
                """, (hashed, customer_id))
            else:
                # Gets current customer info for re-rendering form
                cursor.execute("SELECT * FROM customer_accounts WHERE customer_id = %s", (customer_id,))
                customer = cursor.fetchone()
                cursor.close()
                db.close()
                return render_template('auth/customer_profile.html',
                                       customer=customer,
                                       error="Passwords do not match!")

        db.commit()
        # Updates session with new info
        session['customer_name'] = fullname
        session['customer_email'] = email
        # Gets updated customer info
        cursor.execute("SELECT * FROM customer_accounts WHERE customer_id = %s", (customer_id,))
        customer = cursor.fetchone()
        cursor.close()
        db.close()
        return render_template('auth/customer_profile.html',
                               customer=customer, success="Profile updated successfully!")
    cursor.close()
    db.close()
    return redirect(url_for('customer_auth.customer_profile_settings'))

def order_history():
    customer_id = session.get('customer_id')
    # If user is not logged in, redirect to login
    if not customer_id:
        return redirect(url_for('auth.login_page'))

    db = get_db()
    cursor = db.cursor(dictionary=True)

    # Fetch all orders linked to this customer
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