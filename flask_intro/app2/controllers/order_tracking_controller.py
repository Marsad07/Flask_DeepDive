from flask import render_template, request, session
from app2.database import get_db
from flask_socketio import join_room
from app2 import socketio

def track_order(order_number):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    verified = False
    order = None
    items = []
    error = None

    customer_id = session.get('customer_id')
    if customer_id:
        customer_email = session.get('customer_email')
    else:
        customer_email = request.form.get('guest_email')

    if request.method == 'POST' or customer_id:
        cursor.execute("""
            SELECT * FROM customer_orders 
            WHERE CONCAT('ORD-', DATE_FORMAT(created_at, '%Y%m%d'), '-', 
            LPAD((SELECT COUNT(*) FROM customer_orders co2 
            WHERE DATE(co2.created_at) = DATE(customer_orders.created_at) 
            AND co2.order_id <= customer_orders.order_id), 3, '0')) = %s
        """, (order_number,))
        order = cursor.fetchone()

        if order:
            if customer_id:
                verified = True
            elif customer_email and customer_email.lower() == order['guest_email'].lower():
                verified = True
            else:
                error = "We couldn't find an order with that email. Please try again."
                order = None
        else:
            error = "Order not found"

    if order and verified:
        db2 = get_db()
        cursor2 = db2.cursor(dictionary=True)
        cursor2.execute("SELECT * FROM order_items WHERE order_id = %s", (order['order_id'],))
        items = cursor2.fetchall()
        cursor2.close()
        db2.close()

    cursor.close()
    db.close()

    return render_template(
        'orders/tracking.html',
        order=order,
        items=items,
        error=error,
        order_number=order_number,
        verified=verified
    )
@socketio.on('join_order')
def handle_join(data):
    order_id = data.get('order_id')
    join_room(f'order_{order_id}')