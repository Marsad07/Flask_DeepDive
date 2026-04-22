from flask import render_template, request, redirect, url_for, session
from werkzeug.security import check_password_hash, generate_password_hash
from app2.database import get_db
from app2 import socketio
from flask_socketio import join_room
import secrets
from flask_mailman import EmailMessage

@socketio.on('join_kitchen')
def handle_join_kitchen():
    join_room('kitchen')

def staff_login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM staff_accounts WHERE staff_username = %s AND is_active = 1", (username,))
        staff = cursor.fetchone()

        if staff and check_password_hash(staff['password_hash'], password):
            cursor.execute("UPDATE staff_accounts SET last_login = NOW() WHERE staff_id = %s", (staff['staff_id'],))
            db.commit()
            cursor.close()
            db.close()

            session['staff_id'] = staff['staff_id']
            session['staff_username'] = staff['staff_username']
            session['staff_role'] = staff['role']
            session['staff_name'] = staff['full_name']

            if staff['role'] == 'kitchen':
                return redirect(url_for('staff.kitchen_display'))
            elif staff['role'] == 'driver':
                return redirect(url_for('staff.driver_orders'))
            elif staff['role'] == 'admin':
                session['admin_id'] = staff['staff_id']
                session['admin_username'] = staff['staff_username']
                session['role'] = 'admin'
                return redirect(url_for('admin.dashboard'))
        else:
            cursor.close()
            db.close()
            return render_template("staff/login.html", error="Invalid username or password")

    return render_template("staff/login.html")

def kitchen_display():
    if 'staff_id' not in session or session.get('staff_role') != 'kitchen':
        return redirect(url_for('staff.staff_login'))

    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT co.*, 
               CONCAT('ORD-', DATE_FORMAT(co.created_at, '%Y%m%d'), '-', 
               LPAD((SELECT COUNT(*) FROM customer_orders co2 
               WHERE DATE(co2.created_at) = DATE(co.created_at) 
               AND co2.order_id <= co.order_id), 3, '0')) as order_ref
        FROM customer_orders co
        WHERE co.order_status IN ('confirmed', 'preparing')
        ORDER BY co.created_at ASC
    """)
    orders = cursor.fetchall()
    for order in orders:
        cursor.execute("SELECT * FROM order_items WHERE order_id = %s", (order['order_id'],))
        order['order_items'] = cursor.fetchall()

    cursor.close()
    db.close()
    return render_template('staff/kitchen_display.html', orders=orders,
                           staff_name=session.get('staff_name'))

def staff_logout():
    session.pop('staff_id', None)
    session.pop('staff_username', None)
    session.pop('staff_role', None)
    session.pop('staff_name', None)
    return redirect(url_for('staff.staff_login'))

def kitchen_update_order_status(order_id):
    if 'staff_id' not in session or session.get('staff_role') != 'kitchen':
        return redirect(url_for('staff.staff_login'))

    new_status = request.form.get('status')
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        "UPDATE customer_orders SET order_status = %s WHERE order_id = %s",
        (new_status, order_id)
    )
    db.commit()
    cursor.close()
    db.close()

    socketio.emit('order_status_update', {
        'order_id': order_id,
        'new_status': new_status
    }, room=f'order_{order_id}')

    return redirect(url_for('staff.kitchen_display'))

def driver_orders():
    if 'staff_id' not in session or session.get('staff_role') != 'driver':
        return redirect(url_for('staff.staff_login'))

    driver_id = session['staff_id']
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT is_available FROM staff_accounts WHERE staff_id = %s", (driver_id,))
    driver = cursor.fetchone()

    cursor.execute("""
        SELECT 
            co.order_id,
            co.order_status,
            co.total_price,
            co.special_instructions,
            co.guest_fullname,
            co.guest_phonenum,
            co.guest_delivery_address,
            ca.address_line1, ca.address_line2, ca.city, ca.postcode,
            cust.customer_fullname,
            cust.customer_phonenum AS cust_phonenum
        FROM customer_orders co
        LEFT JOIN customer_accounts cust ON co.customer_id = cust.customer_id
        LEFT JOIN customer_addresses ca ON co.delivery_address_id = ca.address_id
        WHERE co.assigned_driver_id = %s
        AND co.order_status NOT IN ('completed', 'cancelled')
        ORDER BY co.created_at ASC
    """, (driver_id,))
    raw_orders = cursor.fetchall()

    orders = []
    for order in raw_orders:
        cursor.execute("""
            SELECT oi.quantity, oi.item_name as name 
            FROM order_items oi 
            WHERE oi.order_id = %s
        """, (order['order_id'],))
        items = cursor.fetchall()
        customer_name = order['customer_fullname'] or order['guest_fullname'] or 'Guest'
        customer_phone = order['cust_phonenum'] or order['guest_phonenum'] or 'N/A'

        if order['guest_delivery_address']:
            address = order['guest_delivery_address']
        elif order['address_line1']:
            parts = [order['address_line1'], order['address_line2'],
                     order['city'], order['postcode']]
            address = ', '.join(p for p in parts if p)
        else:
            address = 'No address provided'

        orders.append({
            'order_id': order['order_id'],
            'status': order['order_status'],
            'total_price': order['total_price'],
            'delivery_instructions': order['special_instructions'],
            'customer_name': customer_name,
            'customer_phonenum': customer_phone,
            'customer_address': address,
            'order_items': items
        })
    cursor.close()
    db.close()
    return render_template("staff/delivery_driver_display.html",
                           staff_name=session.get('staff_name'),
                           orders=orders,
                           is_available=driver['is_available'],
                           driver_id=driver_id)

def toggle_driver_availability():
    if 'staff_id' not in session or session.get('staff_role') != 'driver':
        return redirect(url_for('staff.staff_login'))

    driver_id = session['staff_id']
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT is_available FROM staff_accounts WHERE staff_id = %s", (driver_id,))
    driver = cursor.fetchone()
    new_status = not driver['is_available']

    cursor.execute("UPDATE staff_accounts SET is_available = %s WHERE staff_id = %s",
                   (new_status, driver_id))
    db.commit()
    cursor.close()
    db.close()
    return redirect(url_for('staff.driver_orders'))

def update_delivery_status(order_id):
    if 'staff_id' not in session or session.get('staff_role') != 'driver':
        return redirect(url_for('staff.staff_login'))

    driver_id = session['staff_id']
    action = request.form.get('action', 'delivered')
    db = get_db()
    cursor = db.cursor(dictionary=True)

    if action == 'pickup':
        cursor.execute("""
            UPDATE customer_orders SET order_status = 'out_for_delivery'
            WHERE order_id = %s AND assigned_driver_id = %s
        """, (order_id, driver_id))
        db.commit()
        cursor.close()
        db.close()
        return redirect(url_for('staff.driver_orders'))

    cursor.execute("""
        UPDATE customer_orders SET order_status = 'completed'
        WHERE order_id = %s AND assigned_driver_id = %s
    """, (order_id, driver_id))

    cursor.execute("""
        SELECT COUNT(*) as active_count FROM customer_orders
        WHERE assigned_driver_id = %s 
        AND order_status NOT IN ('completed', 'cancelled')
    """, (driver_id,))
    result = cursor.fetchone()

    if result['active_count'] == 0:
        cursor.execute("""
            UPDATE staff_accounts SET is_available = TRUE 
            WHERE staff_id = %s
        """, (driver_id,))

    db.commit()
    cursor.close()
    db.close()
    return redirect(url_for('staff.driver_orders'))

def reset_staff_default(staff_id):
    if 'admin_id' not in session:
        return redirect(url_for('staff.staff_login'))

    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT default_staff_password FROM system_settings WHERE id = 1")
    settings = cursor.fetchone()
    default_password = settings['default_staff_password']

    hashed = generate_password_hash(default_password)

    cursor.execute("""
        UPDATE staff_accounts SET password_hash = %s WHERE staff_id = %s
    """, (hashed, staff_id))
    db.commit()

    cursor.close()
    db.close()

    session['toast_message'] = f"Password reset to default ({default_password})"
    return redirect(url_for('admin.edit_staff', staff_id=staff_id))

def reset_staff_email(staff_id):
    if 'admin_id' not in session:
        return redirect(url_for('staff.staff_login'))
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT email FROM staff_accounts WHERE staff_id = %s", (staff_id,))
    staff = cursor.fetchone()
    if not staff or not staff['email']:
        cursor.close()
        db.close()
        session['toast_message'] = "Staff member has no email on file"
        return redirect(url_for('admin.edit_staff', staff_id=staff_id))

    token = secrets.token_urlsafe(32)

    cursor.execute("""
        INSERT INTO password_resets (email, token, created_at)
        VALUES (%s, %s, NOW())
    """, (staff['email'], token))
    db.commit()
    cursor.close()
    db.close()

    reset_link = url_for('staff.staff_reset_password', token=token, _external=True)

    msg = EmailMessage(
        "Reset Your Staff Password",
        f"Click the link below to reset your password:\n\n{reset_link}\n\nThis link expires in 1 hour.",
        to=[staff['email']]
    )
    msg.send()
    session['toast_message'] = "Password reset email sent"
    return redirect(url_for('admin.edit_staff', staff_id=staff_id))

def staff_reset_password(token):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM password_resets WHERE token = %s", (token,))
    reset = cursor.fetchone()

    if not reset:
        cursor.close()
        db.close()
        return "Invalid or expired reset link"

    if request.method == "POST":
        new_password = request.form.get("password")
        hashed = generate_password_hash(new_password)

        cursor.execute("""
            UPDATE staff_accounts SET password_hash = %s
            WHERE email = %s
        """, (hashed, reset['email']))

        cursor.execute("DELETE FROM password_resets WHERE token = %s", (token,))
        db.commit()
        cursor.close()
        db.close()
        return redirect(url_for('staff.staff_login'))

    cursor.close()
    db.close()
    return render_template("staff/reset_password_staff.html", token=token)
