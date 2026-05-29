from flask import request, jsonify, session, current_app
from app2.database import get_db
from datetime import datetime
import stripe

def refund_order(order_id):
    if 'admin_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorised'}), 401

    refund_type    = request.form.get('refund_type', 'full')
    partial_amount = request.form.get('partial_amount', None)

    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM customer_orders WHERE order_id = %s", (order_id,))
    order = cursor.fetchone()

    if not order:
        cursor.close(); db.close()
        return jsonify({'success': False, 'message': 'Order not found'}), 404

    # Guard: already fully refunded
    if order['refund_status'] == 'refunded':
        cursor.close(); db.close()
        return jsonify({'success': False, 'message': 'This order has already been refunded'}), 400

    # Guard: no Stripe intent on record (cash/collection orders)
    if not order['stripe_payment_intent']:
        cursor.close(); db.close()
        return jsonify({'success': False, 'message': 'No Stripe payment found — was this paid by card?'}), 400

    stripe.api_key = current_app.config['STRIPE_SECRET_KEY']

    try:
        if refund_type == 'partial' and partial_amount:
            amount_pence = int(float(partial_amount) * 100)
            refund = stripe.Refund.create(
                payment_intent=order['stripe_payment_intent'],
                amount=amount_pence
            )
            new_refund_status = 'partial'
            refunded_amount   = float(partial_amount)
        else:
            # Full refund — Stripe will refund the entire charge automatically
            refund = stripe.Refund.create(
                payment_intent=order['stripe_payment_intent']
            )
            new_refund_status = 'refunded'
            refunded_amount   = float(order['total_price'])

        cursor.execute("""
            UPDATE customer_orders
            SET refund_status = %s,
                refunded_at   = %s,
                refund_amount = %s,
                order_status  = 'cancelled'
            WHERE order_id = %s
        """, (new_refund_status, datetime.now(), refunded_amount, order_id))
        db.commit()
        cursor.close(); db.close()

        return jsonify({
            'success':   True,
            'refund_id': refund.id,
            'amount':    refunded_amount,
            'status':    new_refund_status
        })

    except stripe.error.InvalidRequestError as e:
        # Catches things like "charge already refunded" from Stripe's side
        cursor.close(); db.close()
        return jsonify({'success': False, 'message': str(e)}), 400

    except stripe.error.StripeError as e:
        cursor.close(); db.close()
        return jsonify({'success': False, 'message': f'Stripe error: {str(e)}'}), 500