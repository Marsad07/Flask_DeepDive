from flask import request, redirect, url_for, flash
import smtplib
import ssl
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def send_contact_email():
    name = request.form['name']
    email = request.form['email']
    subject = request.form['subject']
    message = request.form['message']
    email_to_you = f"""Subject: Contact Form - {subject}

STUDENT INFORMATION:
Name: {name}
Email: {email}

MESSAGE:
{message}

---
Reply directly to: {email}
"""
    confirmation_html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background-color: #FFFDD0; padding: 20px;">
        <div style="max-width: 600px; margin: 0 auto; background-color: white; border: 3px solid #008080; border-radius: 12px; padding: 30px;">
            <h1 style="color: #013d38; text-align: center;">Atlas Desk</h1>
            <h2 style="color: #008080;">Message Received!</h2>

            <p>Hi <strong>{name}</strong>,</p>

            <p>Thank you for contacting Atlas Desk! We've received your message about:</p>

            <div style="background-color: #FFFDD0; border-left: 4px solid #008080; padding: 15px; margin: 20px 0;">
                <strong>"{subject}"</strong>
            </div>

            <p>Our team will review your message and respond within <strong>24-48 hours</strong>.</p>

            <div style="background-color: #008080; color: white; padding: 15px; border-radius: 8px; text-align: center; margin: 20px 0;">
                <p style="margin: 0; font-size: 18px;">⏱️ Expected Response Time</p>
                <p style="margin: 5px 0 0 0; font-size: 24px; font-weight: bold;">24-48 Hours</p>
            </div>

            <p>If you have any urgent concerns, feel free to reply to this email.</p>

            <hr style="border: 1px solid #008080; margin: 20px 0;">

            <p style="text-align: center; color: #666; font-size: 12px;">
                Atlas Desk Support Team<br>
                atlasdesk.contact@gmail.com
            </p>
        </div>
    </body>
    </html>
    """
    try:
        host = "smtp.gmail.com"
        port = 465
        username = "atlasdesk.contact@gmail.com"
        password = "tzeq zsss eyjf pogh"
        context = ssl.create_default_context()

        with smtplib.SMTP_SSL(host, port, context=context) as server:
            server.login(username, password)
            server.sendmail(username, username, email_to_you)

            msg = MIMEMultipart('alternative')
            msg['Subject'] = 'We received your message - Atlas Desk'
            msg['From'] = username
            msg['To'] = email

            html_part = MIMEText(confirmation_html, 'html')
            msg.attach(html_part)

            server.sendmail(username, email, msg.as_string())

        flash("Message sent successfully! Check your email for confirmation.", "success")
        return redirect(url_for('contact.contact_page'))

    except Exception as e:
        print(f"Error: {e}")
        flash("Failed to send message. Please try again.", "error")
        return redirect(url_for('contact.contact_page'))