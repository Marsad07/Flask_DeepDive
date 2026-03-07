from flask import render_template, request, redirect, url_for


def home_page():
    return render_template("homepage.html")


def about_page():
    return render_template("about.html")


def contact_page():
    return render_template("contact.html")

def newsletter_signup():
    if request.method == "POST":
        email = request.form.get("email")
        # i am going to use am email service
        # For now, this will just redirect back
        return redirect(url_for("general.home_page"))
    return redirect(url_for("general.home_page"))