from flask import render_template, request, redirect, url_for, session, current_app, jsonify
from app2.database import get_db, staff_redirect
from datetime import datetime, date
from app2 import socketio, mail
from flask_mailman import EmailMessage
from app2.schemas import CheckoutSchema
from marshmallow import ValidationError
import stripe

@staff_redirect
def checkout_page():
    cart = session.get('cart', {})
    if not cart:
        return redirect(url_for('cart.order_now_menu'))
    total = sum(item['price'] * item['quantity'] for item in cart.values())
    return render_template('checkout/checkout_page.html', cart=cart, total=total,
                           stripe_public_key=current_app.config.get('STRIPE_PUBLIC_KEY'))

def apply_coupon():
    """Validates a coupon code and returns the discount details as JSON."""
    data = request.get_json()
    code = data.get('code', '').strip().upper()
    order_total = float(data.get('total', 0))

    if not code:
        return jsonify({'success': False, 'message': 'Please enter a coupon code.'})

    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM coupons WHERE code = %s", (code,))
    coupon = cursor.fetchone()
    cursor.close()
    db.close()

    # Coupon not found
    if not coupon:
        return jsonify({'success': False, 'message': 'Invalid coupon code.'})

    # Coupon is inactive
    if not coupon['is_active']:
        return jsonify({'success': False, 'message': 'This coupon is no longer active.'})

    # Coupon has expired
    if coupon['expires_at'] and coupon['expires_at'] < date.today():
        return jsonify({'success': False, 'message': 'This coupon has expired.'})

    # Coupon has hit its usage limit
    if coupon['uses_count'] >= coupon['uses_limit']:
        return jsonify({'success': False, 'message': 'This coupon has already been used.'})

    # Calculate discount amount
    if coupon['discount_type'] == 'percent':
        discount_amount = round(order_total * float(coupon['discount_value']) / 100, 2)
    else:
        discount_amount = min(float(coupon['discount_value']), order_total)

    return jsonify({
        'success': True,
        'discount_amount': discount_amount,
        'discount_type': coupon['discount_type'],
        'discount_value': float(coupon['discount_value']),
        'coupon_id': coupon['id'],
    })

@staff_redirect
def process_order():
    # Validate and sanitise form data using Marshmallow before processing
    schema = CheckoutSchema()
    try:
        validated = schema.load(request.form)
    except ValidationError as err:
        # Return first validation error message back to the checkout page
        first_error = next(iter(err.messages.values()))[0]
        cart = session.get('cart', {})
        total = sum(item['price'] * item['quantity'] for item in cart.values())
        return render_template('checkout/checkout_page.html',
                               cart=cart,
                               total=total,
                               stripe_public_key=current_app.config.get('STRIPE_PUBLIC_KEY'),
                               error=first_error)

    full_name            = validated['full_name']
    email                = validated['email']
    phone                = validated['phone']
    order_type           = validated['order_type']
    payment_method       = validated['payment_method']
    special_instructions = validated.get('special_instructions')
    coupon_code          = (validated.get('coupon_code') or '').strip().upper() or None
    discount_amount      = float(validated.get('discount_amount') or 0)

    payment_intent_id   = request.form.get('payment_intent_id')
    payment_status_form = request.form.get('payment_status', 'pending')

    if payment_method == 'card_online' and payment_status_form == 'paid':
        payment_status = 'paid'
    else:
        payment_status = 'pending'

    payment_display = payment_method.replace('_', ' ').title() if payment_method else ''
    customer_id = session.get('customer_id', None)

    delivery_address = None
    if order_type == 'delivery':
        address_line1 = request.form.get('address_line1')
        address_line2 = request.form.get('address_line2')
        city          = request.form.get('city')
        postcode      = request.form.get('postcode')
        parts = [p for p in [address_line1, address_line2, city, postcode] if p]
        delivery_address = ', '.join(parts)

    cart = session.get('cart', {})
    subtotal = sum(item['price'] * item['quantity'] for item in cart.values())
    total = max(0, subtotal - discount_amount)

    db = get_db()
    cursor = db.cursor(dictionary=True)

    # Validate coupon one final time before committing, to prevent race conditions
    coupon_id = None
    if coupon_code:
        cursor.execute("SELECT * FROM coupons WHERE code = %s", (coupon_code,))
        coupon = cursor.fetchone()

        if (coupon and coupon['is_active']
                and coupon['uses_count'] < coupon['uses_limit']
                and (not coupon['expires_at'] or coupon['expires_at'] >= date.today())):
            coupon_id = coupon['id']
        else:
            # Coupon is no longer valid — fall back to full price
            total = subtotal
            discount_amount = 0
            coupon_code = None

    today_str = date.today().strftime('%Y%m%d')
    cursor.execute(
        "SELECT COUNT(*) as count FROM customer_orders WHERE DATE(created_at) = CURDATE()"
    )
    today_count = cursor.fetchone()['count'] + 1
    order_number = f"ORD-{today_str}-{today_count:03d}"

    # stripe_payment_intent saved here so refunds can be issued later from the admin panel
    cursor.execute("""
        INSERT INTO customer_orders 
        (customer_id, guest_fullname, guest_email, guest_phonenum, order_type,
         guest_delivery_address, total_price, order_status, payment_status,
         payment_method, special_instructions, order_date, order_time,
         coupon_code, discount_amount, stripe_payment_intent)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        customer_id, full_name, email, phone, order_type, delivery_address,
        total, 'pending', payment_status, payment_method, special_instructions,
        date.today(), datetime.now().time(), coupon_code, discount_amount,
        payment_intent_id
    ))

    order_id = cursor.lastrowid
    for item_id, item in cart.items():
        cursor.execute("""
            INSERT INTO order_items (order_id, menu_item_id, item_name, item_price, quantity)
            VALUES (%s, %s, %s, %s, %s)
        """, (order_id, int(item_id), item['name'], item['price'], item['quantity']))

    # Increment coupon uses_count now the order is confirmed
    if coupon_id:
        cursor.execute(
            "UPDATE coupons SET uses_count = uses_count + 1 WHERE id = %s",
            (coupon_id,)
        )

    db.commit()
    # Emit new order to kitchen
    socketio.emit('new_order', {'order_id': order_id}, room='kitchen')

    # Send confirmation email — HTML is rendered from a Jinja template, not built inline
    try:
        track_url = url_for('orders.track_order', order_number=order_number, _external=True)
        html_body = render_template(
            'emails/order_confirmation_email.html',
            full_name=full_name,
            order_number=order_number,
            order_type=order_type,
            payment_display=payment_display,
            discount_amount=discount_amount,
            coupon_code=coupon_code,
            total=total,
            track_url=track_url
        )
        msg = EmailMessage(
            subject=f'Order Confirmation - {order_number}',
            body=html_body,
            from_email=None,
            to=[email]
        )
        msg.content_subtype = 'html'
        msg.send()
    except Exception as e:
        print(f"Email error: {e}")

    cursor.close()
    db.close()
    session['cart'] = {}
    return redirect(url_for('checkout.order_confirmation', order_number=order_number))

@staff_redirect
def order_confirmation(order_number):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT * FROM customer_orders 
        WHERE CONCAT('ORD-', DATE_FORMAT(created_at, '%Y%m%d'), '-', 
              LPAD((SELECT COUNT(*) FROM customer_orders co2 
                    WHERE DATE(co2.created_at) = DATE(customer_orders.created_at) 
                    AND co2.order_id <= customer_orders.order_id), 3, '0')) = %s
    """, (order_number,))
    order = cursor.fetchone()

    if not order:
        cursor.close()
        db.close()
        return redirect(url_for('general.home_page'))

    cursor.execute("SELECT * FROM order_items WHERE order_id = %s", (order['order_id'],))
    order_items = cursor.fetchall()
    cursor.close()
    db.close()
    return render_template('checkout/checkout_confirmation.html',
                           order=order,
                           order_items=order_items,
                           order_number=order_number)

@staff_redirect
def create_payment_intent():
    stripe.api_key = current_app.config['STRIPE_SECRET_KEY']
    cart = session.get('cart', {})

    # Reads discount from request body so the intent amount matches what the customer pays
    body = request.get_json(silent=True, force=True) or {}
    discount_amount = float(body.get('discount_amount', 0) or 0)

    subtotal = sum(item['price'] * item['quantity'] for item in cart.values())
    total = max(0, subtotal - discount_amount)

    intent = stripe.PaymentIntent.create(
        amount=int(total * 100),
        currency='gbp',
        payment_method_types=['card'],
    )

    # Return both values — clientSecret for Stripe.js, paymentIntentId to save on the order
    return {'clientSecret': intent.client_secret, 'paymentIntentId': intent.id}