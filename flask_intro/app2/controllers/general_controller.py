from flask import render_template


def home_page():
    return render_template("homepage.html")


def about_page():
    return render_template("about.html")


def contact_page():
    return render_template("contact.html")
