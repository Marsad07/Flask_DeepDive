from flask import render_template
from app2.database import get_db


def show_menu():
    cursor = get_db().cursor(dictionary=True)
    cursor.execute("SELECT * FROM menu_items WHERE is_available = TRUE ORDER BY category, item_name")
    menu_items = cursor.fetchall()
    return render_template("menu.html", menu_items=menu_items)
