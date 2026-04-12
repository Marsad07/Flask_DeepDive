from flask import render_template, request, redirect, url_for
from flask_mailman import EmailMessage
from app2.database import get_db
from app2 import mail
from app2.models.image_model import get_image


def home_page():
    return render_template("homepage.html",
                           hero=get_image("hero"),
                           dish1=get_image("dish1"),
                           dish2=get_image("dish2"),
                           dish3=get_image("dish3"),
    )

def about_page():
    return render_template("about.html")

def contact_page():
    return render_template("contact.html")

def newsletter_signup():
    if request.method == "POST":
        email = request.form.get("email")

        db = get_db()
        cursor = db.cursor()
        try:
            cursor.execute(
                "INSERT INTO newsletter_subs (customer_email) VALUES (%s)",
                (email,)
            )
            db.commit()
            try:
                html_body = f"""<!DOCTYPE html>
                <html>
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                </head>
                <body bgcolor="#F8F4EC" style="margin: 0; padding: 0;">
                    <table width="100%" bgcolor="#F8F4EC" cellpadding="0" cellspacing="0" border="0">
                        <tr>
                            <td align="center" style="padding: 40px 20px;">
                                <table width="600" cellpadding="0" cellspacing="0" border="0"
                                 style="max-width: 600px; width: 100%;">
                                    <tr>
                                        <td bgcolor="#2C2416" align="center" style="padding: 30px;
                                         border-radius: 12px 12px 0 0;">
                                            <h1 style="color: #FFD700; margin: 0; font-size: 28px;
                                             letter-spacing: 3px; font-family: Georgia, serif;">
                                                RESTAURANT NAME
                                            </h1>
                                            <p style="color: #D4AF37; margin: 8px 0 0 0; font-size: 14px;
                                             letter-spacing: 2px; font-family: Georgia, serif;">
                                                NEWSLETTER SUBSCRIPTION
                                            </p>
                                        </td>
                                    </tr>
                                    <tr>
                                        <td bgcolor="#FFFFFF" style="padding: 30px;">
                                            <p style="color: #2C2416; font-size: 16px;
                                             font-family: Georgia, serif; margin: 0 0 10px 0;">
                                                Welcome!
                                            </p>
                                            <p style="color: #5C4033; font-size: 15px; line-height: 1.6;
                                             font-family: Georgia, serif; margin: 0 0 20px 0;">
                                                Thank you for subscribing to our newsletter.
                                                You'll be the first to hear about our latest offers,
                                                new menu items and special events.
                                            </p>
                                            <table width="100%" cellpadding="0" cellspacing="0" border="0"
                                             style="margin: 0 0 20px 0;">
                                                <tr>
                                                    <td bgcolor="#F8F4EC" style="padding: 15px 20px; border-radius: 8px;
                                                     border-left: 4px solid #8B0000;">
                                                        <p style="margin: 0; color: #5C4033; font-size: 13px;
                                                         font-family: Georgia, serif;">
                                                            Subscribed with
                                                        </p>
                                                        <p style="margin: 5px 0 0 0; color: #8B0000; font-size: 16px;
                                                         font-weight: bold; font-family: Georgia, serif;">
                                                            {email}
                                                        </p>
                                                    </td>
                                                </tr>
                                            </table>
                                            <p style="color: #5C4033; font-size: 13px; line-height: 1.6;
                                             font-family: Georgia, serif; margin: 0;">
                                                If you didn't sign up for this, you can safely ignore this email.
                                            </p>
                                        </td>
                                    </tr>
                                    <tr>
                                        <td bgcolor="#2C2416" align="center" style="padding: 20px;
                                         border-radius: 0 0 12px 12px;">
                                            <p style="color: #D4AF37; margin: 0; font-size: 13px;
                                             letter-spacing: 1px; font-family: Georgia, serif;">
                                                © 2026 Restaurant Name. All rights reserved.
                                            </p>
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>
                    </table>
                </body>
                </html>
                """
                msg = EmailMessage(
                    subject='Welcome to our Newsletter!',
                    body=html_body,
                    from_email=None,
                    to=[email]
                )
                msg.content_subtype = 'html'
                msg.send()
            except Exception as e:
                print(f"Newsletter email error: {e}")
            cursor.close()
            db.close()
            return redirect(url_for('general.home_page') + '?newsletter=success')

        except Exception as e:
            print("DB insert error:", e)
            cursor.close()
            db.close()
            return redirect(url_for('general.home_page') + '?newsletter=exists')

    return redirect(url_for('general.home_page'))