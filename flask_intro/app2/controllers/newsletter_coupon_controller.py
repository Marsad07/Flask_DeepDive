from datetime import datetime
from flask import render_template, request, redirect, url_for
from flask_mailman import EmailMessage
from app2.database import get_db
import random
import string
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
        body = request.form.get("body")

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
    cursor.execute("SELECT customer_email, subscribe_time FROM newsletter_subs ORDER BY subscribe_time DESC")
    subscribers = cursor.fetchall()
    cursor.close()
    db.close()

    csv_content = "Email,Subscribed At\n"
    for sub in subscribers:
        csv_content += f"{sub['customer_email']},{sub['subscribe_time']}\n"

    from flask import Response
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
        code = request.form.get("code", "").strip().upper()
        discount_type = request.form.get("discount_type")
        discount_value = request.form.get("discount_value")
        assigned_email = request.form.get("assigned_email", "").strip() or None
        uses_limit = request.form.get("uses_limit", 1)
        expires_at = request.form.get("expires_at") or None

        # Auto generate code if left blank
        if not code:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

        db = get_db()
        cursor = db.cursor()
        try:
            cursor.execute("""
                INSERT INTO coupons
                (code, discount_type, discount_value, assigned_email, uses_limit, expires_at)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (code, discount_type, discount_value, assigned_email, uses_limit, expires_at))
            db.commit()

            # If assigned to an email, send them the code
            if assigned_email:
                try:
                    discount_display = (
                        f"{discount_value}%" if discount_type == "percent"
                        else f"£{discount_value}"
                    )
                    html_body = f"""
                    <body bgcolor="#F8F4EC" style="margin:0;padding:0;font-family:Georgia,serif;">
                        <table width="100%" bgcolor="#F8F4EC" cellpadding="0" cellspacing="0">
                            <tr><td align="center" style="padding:40px 20px;">
                                <table width="600" cellpadding="0" cellspacing="0"
                                       style="max-width:600px;width:100%;">
                                    <tr>
                                        <td bgcolor="#2C2416" align="center"
                                            style="padding:30px;border-radius:12px 12px 0 0;">
                                            <h1 style="color:#FFD700;margin:0;font-size:28px;
                                                       letter-spacing:3px;">
                                                You've got a discount!
                                            </h1>
                                        </td>
                                    </tr>
                                    <tr>
                                        <td bgcolor="#FFFFFF" style="padding:30px;">
                                            <p style="color:#2C2416;font-size:16px;margin:0 0 16px;">
                                                Here is your exclusive discount code:
                                            </p>
                                            <div style="background:#F8F4EC;border-left:4px solid #8B0000;
                                                        padding:20px;border-radius:8px;
                                                        text-align:center;margin-bottom:20px;">
                                                <p style="font-size:32px;font-weight:bold;
                                                          color:#8B0000;margin:0;
                                                          letter-spacing:4px;">
                                                    {code}
                                                </p>
                                                <p style="color:#5C4033;font-size:14px;margin:8px 0 0;">
                                                    {discount_display} off your order
                                                </p>
                                            </div>
                                            <p style="color:#5C4033;font-size:13px;margin:0;">
                                                Use this code at checkout. 
                                                {'Expires ' + expires_at if expires_at else 'No expiry date.'}
                                            </p>
                                        </td>
                                    </tr>
                                    <tr>
                                        <td bgcolor="#2C2416" align="center"
                                            style="padding:20px;border-radius:0 0 12px 12px;">
                                            <p style="color:#D4AF37;margin:0;font-size:13px;">
                                                © 2026 Restaurant. All rights reserved.
                                            </p>
                                        </td>
                                    </tr>
                                </table>
                            </td></tr>
                        </table>
                    </body>
                    """
                    msg = EmailMessage(
                        subject='Your Exclusive Discount Code',
                        body=html_body,
                        from_email=None,
                        to=[assigned_email]
                    )
                    msg.content_subtype = 'html'
                    msg.send()
                except Exception as e:
                    print(f"Coupon email error: {e}")

        except Exception as e:
            print(f"Coupon create error: {e}")
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