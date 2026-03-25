from flask import render_template, request, redirect, url_for, session
from app2.database import restaurant_db1
from datetime import datetime, date

def checkout_page():
    # This checks if cart is empty
    cart = session.get('cart', {})
    if not cart:
        return redirect(url_for('cart.order_now_menu'))

    # This calculates total
    total = sum(item['price'] * item['quantity'] for item in cart.values())

    return render_template('checkout/checkout_page.html', cart=cart, total=total)

def process_order():
    # This gets form data
    full_name = request.form.get('full_name')
    email = request.form.get('email')
    phone = request.form.get('phone')
    order_type = request.form.get('order_type')
    payment_method = request.form.get('payment_method')
    special_instructions = request.form.get('special_instructions')

    # This gets delivery address if delivery
    delivery_address = None
    if order_type == 'delivery':
        address_line1 = request.form.get('address_line1')
        address_line2 = request.form.get('address_line2')
        city = request.form.get('city')
        postcode = request.form.get('postcode')
        delivery_address = f"{address_line1}, {address_line2}, {city}, {postcode}"

    # This gets cart and calculates total
    cart = session.get('cart', {})
    total = sum(item['price'] * item['quantity'] for item in cart.values())

    # This generates order number (format: ORD-YYYYMMDD-XXX)
    cursor = restaurant_db1.cursor(dictionary=True)
    today_str = date.today().strftime('%Y%m%d')

    # This gets count of orders today to generate sequential number
    cursor.execute("""
        SELECT COUNT(*) as count FROM customer_orders 
        WHERE DATE(created_at) = CURDATE()
    """)
    today_count = cursor.fetchone()['count'] + 1
    order_number = f"ORD-{today_str}-{today_count:03d}"

    # This inserts order into customer_orders table
    cursor.execute("""
        INSERT INTO customer_orders 
        (guest_fullname, guest_email, guest_phonenum, order_type, 
         guest_delivery_address, total_price, order_status, payment_status, 
         payment_method, special_instructions, order_date, order_time)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        full_name, email, phone, order_type, delivery_address,
        total, 'pending', 'pending', payment_method, special_instructions,
        date.today(), datetime.now().time()
    ))

    # This gets the order_id that was just created
    order_id = cursor.lastrowid

    # This inserts each cart item into order_items table
    for item_id, item in cart.items():
        cursor.execute("""
            INSERT INTO order_items 
            (order_id, menu_item_id, item_name, item_price, quantity)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            order_id, int(item_id), item['name'], item['price'], item['quantity']
        ))

    # This commits all changes to database
    restaurant_db1.commit()

    # This clears the cart
    session['cart'] = {}

    # This redirects to confirmation page with order number
    return redirect(url_for('checkout.order_confirmation', order_number=order_number))

def order_confirmation(order_number):
    # This gets order details from database
    cursor = restaurant_db1.cursor(dictionary=True)
    cursor.execute("""
        SELECT * FROM customer_orders 
        WHERE CONCAT('ORD-', DATE_FORMAT(created_at, '%Y%m%d'), '-', 
              LPAD((SELECT COUNT(*) FROM customer_orders co2 
                    WHERE DATE(co2.created_at) = DATE(customer_orders.created_at) 
                    AND co2.order_id <= customer_orders.order_id), 3, '0')) = %s
    """, (order_number,))
    order = cursor.fetchone()

    if not order:
        return redirect(url_for('general.home_page'))

    # This gets order items
    cursor.execute("""
        SELECT * FROM order_items 
        WHERE order_id = %s
    """, (order['order_id'],))
    order_items = cursor.fetchall()

    return render_template('checkout/checkout_confirmation.html',
                           order=order,
                           order_items=order_items,
                           order_number=order_number)