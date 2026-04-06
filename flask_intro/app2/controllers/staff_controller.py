from flask import render_template, request, redirect, url_for, session
from werkzeug.security import check_password_hash
from app2.database import get_db
from app2 import socketio
from flask_socketio import join_room

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
    return render_template('staff/kitchen_display.html', orders=orders, staff_name=session.get('staff_name'))

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