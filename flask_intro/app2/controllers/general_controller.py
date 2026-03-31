from flask import render_template, request, redirect, url_for
from app2.database import get_db

def home_page():
    return render_template("homepage.html")


def about_page():
    return render_template("about.html")


def contact_page():
    return render_template("contact.html")

def newsletter_signup():
    if request.method == "POST":
        email = request.form.get("email")

        cursor = get_db().cursor()
        try:
            cursor.execute("INSERT INTO newsletter_subs (customer_email) VALUES (%s)", (email,))
            get_db().commit()
            # Saves email
            return redirect(url_for('general.home_page') + '?newsletter=success')
        except:
            # Condition to check is the email was already used or not
            return redirect(url_for('general.home_page') + '?newsletter=exists')

    return redirect(url_for('general.home_page'))