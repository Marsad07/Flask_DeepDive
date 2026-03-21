from flask import render_template, request, redirect, url_for, session
from app2.database import restaurant_db1

def order_now_menu():
    cursor = restaurant_db1.cursor(dictionary=True)
    cursor.execute("""
        SELECT * FROM menu_items 
        WHERE is_available = TRUE 
        AND available_for_delivery = TRUE
    """)
    items = cursor.fetchall()
    return render_template("menu2.html", menu_items=items)


def view_cart():
    # This gets cart from session
    cart = session.get('cart', {})
    # This calculates total price (handle empty cart)
    total = 0
    if cart:
        total = sum(float(item['price']) * int(item['quantity']) for item in cart.values())
    return render_template("cart/view_cart.html", cart=cart, total=total)

def add_to_cart(item_id):
    quantity = int(request.form.get("quantity"))

    # This fetches the item from the database
    cursor = restaurant_db1.cursor(dictionary=True)
    cursor.execute("SELECT * FROM menu_items WHERE item_id = %s", (item_id,))
    item = cursor.fetchone()

    # This is for if the item is not found
    if not item:
        return redirect(url_for('menu.show_menu') + '?error=item_not_found')

    # This is for if the item is unavailable
    if not item['is_available']:
        return redirect(url_for('menu.show_menu') + '?error=item_not_available')

    # This is for delivery availability check
    if 'available_for_delivery' in item and not item['available_for_delivery']:
        return redirect(url_for('menu.show_menu') + '?error=dine_in_only')

    # This loads cart from session
    cart = session.get('cart', {})
    item_key = str(item_id)

    # If item already in cart, the customer can increase quantity
    if item_key in cart:
        cart[item_key]['quantity'] += quantity
    else:
        # This is for adding new item to cart
        cart[item_key] = {
            'name': item['item_name'],
            'price': float(item['price']),
            'quantity': quantity
        }

    # This saves cart back to session
    session['cart'] = cart
    session['cart_message'] = f"✓ {item['item_name']} added to cart!"
    return redirect(url_for('cart.order_now_menu'))


#def update_cart():


def remove_from_cart(item_id):
    cart = session.get('cart', {})
    item_key = str(item_id)

    if item_key in cart:
        del cart[item_key]

    session['cart'] = cart
    return redirect(url_for('cart.view_cart'))
#def clear_cart():

