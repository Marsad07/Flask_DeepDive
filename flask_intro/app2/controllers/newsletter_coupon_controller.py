from datetime import datetime
from flask import render_template, request, redirect, url_for, Response
from flask_mailman import EmailMessage
from app2.database import get_db
from app2.schemas import CouponCreateSchema
from marshmallow import ValidationError
import random
import string
import traceback
from datetime import date

# Newsletter
def manage_newsletter():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM newsletter_subs ORDER BY subscribe_time DESC")
    subscribers = cursor.fetchall()
    cursor.close()
    db.close()
    return render_template("admin/manage_newsletter_subs.html", subscribers=subscribers,
                           now_month=datetime.now().strftime('%Y-%m'))

def delete_newsletter_subscriber(email):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM newsletter_subs WHERE customer_email = %s", (email,))
    db.commit()
    cursor.close()
    db.close()
    return redirect(url_for('admin.manage_newsletter'))

def send_newsletter():
    if request.method == "POST":
        subject = request.form.get("subject")
        body    = request.form.get("body")

        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT customer_email FROM newsletter_subs")
        subscribers = cursor.fetchall()
        cursor.close()
        db.close()

        sent = 0
        failed = 0
        for sub in subscribers:
            try:
                msg = EmailMessage(
                    subject=subject,
                    body=body,
                    from_email=None,
                    to=[sub['customer_email']]
                )
                msg.content_subtype = 'html'
                msg.send()
                sent += 1
            except Exception as e:
                print(f"Failed to send to {sub['customer_email']}: {e}")
                failed += 1

        return redirect(
            url_for('admin.manage_newsletter') + f'?sent={sent}&failed={failed}'
        )
    return redirect(url_for('admin.manage_newsletter'))

def export_subscribers():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        "SELECT customer_email, subscribe_time FROM newsletter_subs ORDER BY subscribe_time DESC"
    )
    subscribers = cursor.fetchall()
    cursor.close()
    db.close()

    csv_content = "Email,Subscribed At\n"
    for sub in subscribers:
        csv_content += f"{sub['customer_email']},{sub['subscribe_time']}\n"

    return Response(
        csv_content,
        mimetype='text/csv',
        headers={"Content-Disposition": "attachment; filename=subscribers.csv"}
    )

# Coupons
def manage_coupons():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM coupons ORDER BY created_at DESC")
    coupons = cursor.fetchall()
    cursor.execute("SELECT customer_email FROM newsletter_subs")
    subscribers = cursor.fetchall()
    cursor.execute("SELECT customer_fullname, customer_email FROM customer_accounts")
    customers = cursor.fetchall()
    cursor.close()
    db.close()
    return render_template('admin/coupons.html',
                           coupons=coupons,
                           subscribers=subscribers,
                           customers=customers,
                           today=date.today())

def create_coupon():
    if request.method == "POST":
        print("DEBUG form data:", dict(request.form))

        schema = CouponCreateSchema()
        try:
            validated = schema.load(request.form)
            print("DEBUG validated:", validated)
        except ValidationError as err:
            print("DEBUG validation error:", err.messages)
            first_error = next(iter(err.messages.values()))[0]
            db = get_db()
            cursor = db.cursor(dictionary=True)
            cursor.execute("SELECT * FROM coupons ORDER BY created_at DESC")
            coupons = cursor.fetchall()
            cursor.execute("SELECT customer_email FROM newsletter_subs")
            subscribers = cursor.fetchall()
            cursor.execute("SELECT customer_fullname, customer_email FROM customer_accounts")
            customers = cursor.fetchall()
            cursor.close()
            db.close()
            return render_template('admin/coupons.html',
                                   coupons=coupons,
                                   subscribers=subscribers,
                                   customers=customers,
                                   today=date.today(),
                                   error=first_error)

        code           = validated.get('code') or ''.join(
                            random.choices(string.ascii_uppercase + string.digits, k=8)
                         )
        discount_type  = validated['discount_type']
        discount_value = validated['discount_value']
        assigned_email = validated.get('assigned_email') or None
        uses_limit     = validated.get('uses_limit', 1)
        expires_at     = validated.get('expires_at')
        send_to        = validated.get('send_to', 'none')

        if assigned_email == '':
            assigned_email = None

        print(f"DEBUG code={code} type={discount_type} value={discount_value} send_to={send_to} assigned={assigned_email}")

        if discount_type == 'percent' and discount_value > 100:
            db = get_db()
            cursor = db.cursor(dictionary=True)
            cursor.execute("SELECT * FROM coupons ORDER BY created_at DESC")
            coupons = cursor.fetchall()
            cursor.execute("SELECT customer_email FROM newsletter_subs")
            subscribers = cursor.fetchall()
            cursor.execute("SELECT customer_fullname, customer_email FROM customer_accounts")
            customers = cursor.fetchall()
            cursor.close()
            db.close()
            return render_template('admin/coupons.html',
                                   coupons=coupons,
                                   subscribers=subscribers,
                                   customers=customers,
                                   today=date.today(),
                                   error="Percent discount cannot exceed 100%.")

        # Build list of emails to send to based on send_to selection
        bulk_emails = []
        if send_to in ('all_subscribers', 'all_everyone'):
            db2 = get_db()
            cursor2 = db2.cursor(dictionary=True)
            cursor2.execute("SELECT customer_email FROM newsletter_subs")
            bulk_emails += [r['customer_email'] for r in cursor2.fetchall()]
            cursor2.close()
            db2.close()
        if send_to in ('all_customers', 'all_everyone'):
            db2 = get_db()
            cursor2 = db2.cursor(dictionary=True)
            cursor2.execute("SELECT customer_email FROM customer_accounts")
            bulk_emails += [r['customer_email'] for r in cursor2.fetchall()]
            cursor2.close()
            db2.close()
        if send_to == 'one' and assigned_email:
            bulk_emails = [assigned_email]

        bulk_emails = list(set(bulk_emails))
        print(f"DEBUG bulk_emails: {bulk_emails}")

        db = get_db()
        cursor = db.cursor()
        try:
            if bulk_emails:
                for recipient_email in bulk_emails:
                    unique_code = ''.join(
                        random.choices(string.ascii_uppercase + string.digits, k=8)
                    )
                    print(f"DEBUG inserting coupon {unique_code} for {recipient_email}")
                    cursor.execute("""
                        INSERT INTO coupons
                        (code, discount_type, discount_value, assigned_email, uses_limit, expires_at)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (unique_code, discount_type, discount_value,
                          recipient_email, 1, expires_at))
                    db.commit()

                    try:
                        discount_display = (
                            f"{discount_value}%" if discount_type == "percent"
                            else f"£{discount_value}"
                        )
                        html_body = render_template(
                            'emails/coupon_email.html',
                            code=unique_code,
                            discount_display=discount_display,
                            expires_at=expires_at
                        )
                        msg = EmailMessage(
                            subject='Your Exclusive Discount Code',
                            body=html_body,
                            from_email=None,
                            to=[recipient_email]
                        )
                        msg.content_subtype = 'html'
                        msg.send()
                        print(f"DEBUG email sent to {recipient_email}")
                    except Exception as e:
                        print(f"Coupon email error for {recipient_email}: {e}")
                        traceback.print_exc()
            else:
                print(f"DEBUG inserting single coupon {code}")
                cursor.execute("""
                    INSERT INTO coupons
                    (code, discount_type, discount_value, assigned_email, uses_limit, expires_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (code, discount_type, discount_value, assigned_email, uses_limit, expires_at))
                db.commit()
                print("DEBUG single coupon inserted")

        except Exception as e:
            print(f"Coupon create error: {e}")
            traceback.print_exc()
        finally:
            cursor.close()
            db.close()

    return redirect(url_for('admin.manage_coupons'))

def delete_coupon(coupon_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM coupons WHERE id = %s", (coupon_id,))
    db.commit()
    cursor.close()
    db.close()
    return redirect(url_for('admin.manage_coupons'))

def toggle_coupon(coupon_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "UPDATE coupons SET is_active = NOT is_active WHERE id = %s",
        (coupon_id,)
    )
    db.commit()
    cursor.close()
    db.close()
    return redirect(url_for('admin.manage_coupons'))