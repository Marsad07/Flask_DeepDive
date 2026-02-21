from flask import render_template
from app2.models.menu import get_all_menu_items

def show_menu():
    items = get_all_menu_items()
    return render_template("menu.html", items=items)