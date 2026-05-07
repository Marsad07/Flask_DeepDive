from flask import render_template, request, redirect, url_for, session, current_app, jsonify
from app2.database import get_db, staff_redirect
from datetime import datetime, date
from app2 import socketio, mail
from flask_mailman import EmailMessage
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
    full_name = request.form.get('full_name')
    email = request.form.get('email')
    phone = request.form.get('phone')
    order_type = request.form.get('order_type')
    payment_intent_id = request.form.get('payment_intent_id')
    payment_status_form = request.form.get('payment_status', 'pending')
    payment_method = request.form.get('payment_method')
    special_instructions = request.form.get('special_instructions')
    coupon_code = request.form.get('coupon_code', '').strip().upper() or None
    discount_amount = float(request.form.get('discount_amount', 0) or 0)

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
        city = request.form.get('city')
        postcode = request.form.get('postcode')
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

    cursor.execute("""
        INSERT INTO customer_orders 
        (customer_id, guest_fullname, guest_email, guest_phonenum, order_type,
         guest_delivery_address, total_price, order_status, payment_status,
         payment_method, special_instructions, order_date, order_time,
         coupon_code, discount_amount)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        customer_id, full_name, email, phone, order_type, delivery_address,
        total, 'pending', payment_status, payment_method, special_instructions,
        date.today(), datetime.now().time(), coupon_code, discount_amount
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

    # Send confirmation email
    try:
        discount_row = ""
        if discount_amount > 0:
            discount_row = f"""
                <tr>
                    <td style="padding:10px 0;color:#5C4033;font-size:14px;
                     font-family:Georgia,serif;border-bottom:1px solid #E8DFD0;">
                        Discount ({coupon_code})
                    </td>
                    <td align="right" style="padding:10px 0;color:#28a745;font-weight:bold;
                     font-size:14px;font-family:Georgia,serif;border-bottom:1px solid #E8DFD0;">
                        -£{discount_amount:.2f}
                    </td>
                </tr>"""
        track_url = url_for('orders.track_order', order_number=order_number, _external=True)
        html_body = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="color-scheme" content="light only">
    <meta name="supported-color-schemes" content="light">
    <style>
        @media (prefers-color-scheme: dark) {{
            .email-body {{ background-color: #1A1410 !important; color: #FFFEF2 !important; }}
            .order-ref-box {{ background-color: var(--color-text) !important; }}
            p {{ color: #FFFEF2 !important; }}
        }}
    </style>
</head>
<body bgcolor="#F8F4EC" style="margin:0;padding:0;">
    <table width="100%" bgcolor="#F8F4EC" cellpadding="0" cellspacing="0" border="0">
        <tr>
            <td align="center" style="padding:40px 20px;">
                <table width="600" cellpadding="0" cellspacing="0" border="0"
                       style="max-width:600px;width:100%;">
                    <tr>
                        <td bgcolor="#2C2416" align="center"
                            style="padding:30px;border-radius:12px 12px 0 0;">
                            <h1 style="color:#FFD700;margin:0;font-size:28px;
                             letter-spacing:3px;font-family:Georgia,serif;">
                                RESTAURANT NAME
                            </h1>
                            <p style="color:#D4AF37;margin:8px 0 0;font-size:14px;
                             letter-spacing:2px;font-family:Georgia,serif;">
                                ORDER CONFIRMATION
                            </p>
                        </td>
                    </tr>
                    <tr>
                        <td class="email-body" bgcolor="#FFFFFF" style="padding:30px;">
                            <p style="color:#2C2416;font-size:16px;font-family:Georgia,serif;
                             margin:0 0 10px;">
                                Hi <strong>{full_name}</strong>,
                            </p>
                            <p style="color:#5C4033;font-size:15px;line-height:1.6;
                             font-family:Georgia,serif;margin:0 0 20px;">
                                Thank you for your order! We've received it and will get started soon.
                            </p>
                            <table width="100%" cellpadding="0" cellspacing="0" border="0"
                                   style="margin:0 0 20px;">
                                <tr>
                                    <td class="order-ref-box" bgcolor="#F8F4EC"
                                        style="padding:15px 20px;border-radius:8px;
                                         border-left:4px solid #8B0000;">
                                        <p style="margin:0;color:#5C4033;font-size:13px;
                                         font-family:Georgia,serif;letter-spacing:1px;">
                                            ORDER REFERENCE
                                        </p>
                                        <p style="margin:5px 0 0;color:#8B0000;font-size:22px;
                                         font-weight:bold;font-family:Georgia,serif;">
                                            {order_number}
                                        </p>
                                    </td>
                                </tr>
                            </table>
                            <table width="100%" cellpadding="0" cellspacing="0" border="0">
                                <tr>
                                    <td style="padding:10px 0;color:#5C4033;font-size:14px;
                                     font-family:Georgia,serif;border-bottom:1px solid #E8DFD0;">
                                        Order Type
                                    </td>
                                    <td align="right" style="padding:10px 0;color:#2C2416;
                                     font-weight:bold;font-size:14px;font-family:Georgia,serif;
                                     border-bottom:1px solid #E8DFD0;">
                                        {order_type.capitalize()}
                                    </td>
                                </tr>
                                <tr>
                                    <td style="padding:10px 0;color:#5C4033;font-size:14px;
                                     font-family:Georgia,serif;border-bottom:1px solid #E8DFD0;">
                                        Payment
                                    </td>
                                    <td align="right" style="padding:10px 0;color:#2C2416;
                                     font-weight:bold;font-size:14px;font-family:Georgia,serif;
                                     border-bottom:1px solid #E8DFD0;">
                                        {payment_display}
                                    </td>
                                </tr>
                                {discount_row}
                                <tr>
                                    <td style="padding:10px 0;color:#5C4033;font-size:14px;
                                     font-family:Georgia,serif;">
                                        Total
                                    </td>
                                    <td align="right" style="padding:10px 0;color:#8B0000;
                                     font-weight:bold;font-size:18px;font-family:Georgia,serif;">
                                        £{total:.2f}
                                    </td>
                                </tr>
                            </table>
                            <table width="100%" cellpadding="0" cellspacing="0" border="0"
                                   style="margin:30px 0;">
                                <tr>
                                <td align="center">
                                    <a href="{track_url}"
                                       style="background-color:#8B0000;color:#FFD700;
                                        padding:14px 35px;text-decoration:none;border-radius:8px;
                                        font-size:15px;font-weight:bold;letter-spacing:2px;
                                        text-transform:uppercase;font-family:Georgia,serif;
                                        display:inline-block;">
                                        TRACK YOUR ORDER
                                    </a>
                                </td>
                            </tr>
                            </table>
                            <p style="color:#5C4033;font-size:14px;line-height:1.6;
                             font-family:Georgia,serif;margin:0;">
                                If you have any questions about your order, please don't hesitate
                                to contact us.
                            </p>
                        </td>
                    </tr>
                    <tr>
                        <td bgcolor="#2C2416" align="center"
                            style="padding:20px;border-radius:0 0 12px 12px;">
                            <p style="color:#D4AF37;margin:0;font-size:13px;
                             letter-spacing:1px;font-family:Georgia,serif;">
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
    total = sum(item['price'] * item['quantity'] for item in cart.values())
    intent = stripe.PaymentIntent.create(
        amount=int(total * 100),
        currency='gbp',
        payment_method_types=['card'],
    )
    return {'clientSecret': intent.client_secret}