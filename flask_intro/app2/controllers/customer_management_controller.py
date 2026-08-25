from flask import render_template, request, redirect, url_for, session, flash
from app2.database import get_db
from werkzeug.security import generate_password_hash

def view_all_customers():
    if 'admin_id' not in session:
        return redirect(url_for('admin.admin_login'))

    db = get_db()
    cursor = db.cursor(dictionary=True)

    search      = request.args.get('search', '').strip()
    filter_type = request.args.get('filter', '')

    # This builds the customer list with order stats joined
    base_query = """
        SELECT 
            ca.customer_id,
            ca.customer_fullname,
            ca.customer_email,
            ca.customer_phonenum,
            ca.is_active,
            ca.account_creation,
            COUNT(co.order_id)               AS total_orders,
            COALESCE(SUM(co.total_price), 0) AS total_spent,
            MAX(co.created_at)               AS last_order_date
        FROM customer_accounts ca
        LEFT JOIN customer_orders co ON co.customer_id = ca.customer_id
    """
    conditions = []
    params     = []

    if search:
        conditions.append("""
            (ca.customer_fullname LIKE %s
             OR ca.customer_email LIKE %s
             OR ca.customer_phonenum LIKE %s)
        """)
        like = f"%{search}%"
        params.extend([like, like, like])

    if filter_type == 'active':
        conditions.append("ca.is_active = 1")
    elif filter_type == 'disabled':
        conditions.append("ca.is_active = 0")

    if conditions:
        base_query += " WHERE " + " AND ".join(conditions)

    base_query += " GROUP BY ca.customer_id ORDER BY ca.account_creation DESC"

    cursor.execute(base_query, params)
    customers = cursor.fetchall()

    # Summary counts for stat cards
    cursor.execute("SELECT COUNT(*) AS c FROM customer_accounts")
    total_count = cursor.fetchone()['c']

    cursor.execute("SELECT COUNT(*) AS c FROM customer_accounts WHERE is_active = 1")
    active_count = cursor.fetchone()['c']

    cursor.execute("""
        SELECT COUNT(*) AS c FROM customer_accounts 
        WHERE account_creation >= DATE_SUB(NOW(), INTERVAL 30 DAY)
    """)
    new_this_month = cursor.fetchone()['c']

    cursor.close()
    db.close()

    return render_template(
        'admin/view_all_customers.html',
        customers=customers,
        search=search,
        filter_type=filter_type,
        total_count=total_count,
        active_count=active_count,
        new_this_month=new_this_month
    )


def view_customer_profile(customer_id):
    if 'admin_id' not in session:
        return redirect(url_for('admin.admin_login'))

    db = get_db()
    cursor = db.cursor(dictionary=True)

    # This gets the customer account details
    cursor.execute("""
        SELECT * FROM customer_accounts WHERE customer_id = %s
    """, (customer_id,))
    customer = cursor.fetchone()

    if not customer:
        cursor.close()
        db.close()
        return redirect(url_for('admin.view_all_customers'))

    # This gets order stats for the customer
    cursor.execute("""
        SELECT 
            COUNT(*) AS total_orders,
            COALESCE(SUM(total_price), 0) AS total_spent,
            MAX(created_at) AS last_order_date
        FROM customer_orders
        WHERE customer_id = %s
    """, (customer_id,))
    stats = cursor.fetchone()

    # This gets the customer's favourite item by quantity ordered
    cursor.execute("""
        SELECT oi.item_name, SUM(oi.quantity) AS total_qty
        FROM order_items oi
        JOIN customer_orders co ON oi.order_id = co.order_id
        WHERE co.customer_id = %s
        GROUP BY oi.item_name
        ORDER BY total_qty DESC
        LIMIT 1
    """, (customer_id,))
    fav = cursor.fetchone()
    fav_item = fav['item_name'] if fav else '—'

    # This gets the full order history for the customer
    cursor.execute("""
        SELECT 
            order_id,
            order_type,
            order_status,
            payment_status,
            payment_method,
            total_price,
            created_at,
            CONCAT('ORD-', DATE_FORMAT(created_at, '%%Y%%m%%d'), '-',
                LPAD((SELECT COUNT(*) FROM customer_orders co2
                      WHERE DATE(co2.created_at) = DATE(customer_orders.created_at)
                      AND co2.order_id <= customer_orders.order_id), 3, '0')
            ) AS order_number
        FROM customer_orders
        WHERE customer_id = %s
        ORDER BY created_at DESC
    """, (customer_id,))
    orders = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template(
        'admin/view_customer_profile.html',
        customer=customer,
        stats=stats,
        fav_item=fav_item,
        orders=orders
    )


def edit_customer(customer_id):
    if 'admin_id' not in session:
        return redirect(url_for('admin.admin_login'))

    if request.method == 'POST':
        fullname = request.form.get('customer_fullname', '').strip()
        email    = request.form.get('customer_email', '').strip()
        phone    = request.form.get('customer_phonenum', '').strip()

        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
            UPDATE customer_accounts
            SET customer_fullname = %s, customer_email = %s, customer_phonenum = %s
            WHERE customer_id = %s
        """, (fullname, email, phone, customer_id))
        db.commit()
        cursor.close()
        db.close()

        flash('Customer details updated successfully.', 'success')

    return redirect(url_for('admin.view_customer_profile', customer_id=customer_id))


def toggle_customer_active(customer_id):
    if 'admin_id' not in session:
        return redirect(url_for('admin.admin_login'))

    db = get_db()
    cursor = db.cursor(dictionary=True)

    # This toggles the is_active flag on the customer account
    cursor.execute("""
        SELECT is_active FROM customer_accounts WHERE customer_id = %s
    """, (customer_id,))
    customer = cursor.fetchone()

    if customer:
        new_status = 0 if customer['is_active'] else 1
        cursor.execute("""
            UPDATE customer_accounts SET is_active = %s WHERE customer_id = %s
        """, (new_status, customer_id))
        db.commit()
        flash(
            'Customer account enabled.' if new_status else 'Customer account disabled.',
            'success'
        )

    cursor.close()
    db.close()
    return redirect(url_for('admin.view_customer_profile', customer_id=customer_id))

def reset_customer_password(customer_id):
    if 'admin_id' not in session:
        return redirect(url_for('admin.admin_login'))

    new_password = request.form.get('new_password', '').strip()
    if new_password:
        hashed = generate_password_hash(new_password)
        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
            UPDATE customer_accounts SET customer_password_hash = %s
            WHERE customer_id = %s
        """, (hashed, customer_id))
        db.commit()
        cursor.close()
        db.close()
        flash('Customer password reset successfully.', 'success')

    return redirect(url_for('admin.view_customer_profile', customer_id=customer_id))