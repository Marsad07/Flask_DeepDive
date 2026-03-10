from flask import render_template
from app2.database import restaurant_db1


def show_menu():
    cursor = restaurant_db1.cursor(dictionary=True)
    cursor.execute("SELECT * FROM menu_items WHERE is_available = TRUE ORDER BY category, item_name")
    menu_items = cursor.fetchall()
    return render_template("menu.html", menu_items=menu_items)
