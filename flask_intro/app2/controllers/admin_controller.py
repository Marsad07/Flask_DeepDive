from flask import render_template, request, redirect, url_for, session
from app2.database import restaurant_db1

def admin_login():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']

        # This checks for the users credentials
        cursor = restaurant_db1.cursor(dictionary=True)
        cursor.execute("SELECT * FROM admin_restaurant WHERE admin_username = %s", (username,)        )
        admin = cursor.fetchone()

        # This verifies the password
        if admin and admin['password_hash'] == password:
            # This will be for successful login
            session['admin_id'] = admin['admin_id']
            session['admin_username'] = admin['admin_username']
            session['role'] = admin['role']

            # This updates the last login that happened
            cursor.execute(
                "UPDATE admin_restaurant SET last_login = NOW() WHERE admin_id = %s",
                (admin['admin_id'],)
            )
            restaurant_db1.commit()
            return redirect(url_for('admin.dashboard'))
        else:
            # This is for if the login failed
            return render_template('admin/login.html', error="Incorrect username or password")

    return render_template('admin/login.html')

def dashboard():
    # This checks if the user is logged in or not
    if 'admin_id' not in session:
        return redirect(url_for('admin.admin_login'))
    cursor = restaurant_db1.cursor(dictionary=True)

    # This will get the books from today / current day
    cursor.execute("SELECT COUNT(*) as count FROM reservations_restaurant "
                   "WHERE reservation_date = CURDATE()")
    today_bookings = cursor.fetchone()['count']

    # This will get the count of total bookings
    cursor.execute("SELECT COUNT(*) as count FROM reservations_restaurant")
    total_bookings = cursor.fetchone()['count']

    # This will get newsletter subscribers
    newsletter_subs = 0

    # This will show / get the  most recent 5 reservations
    cursor.execute("""
            SELECT * FROM reservations_restaurant 
            ORDER BY reservation_createdate DESC 
            LIMIT 5
        """)
    recent_reservations = cursor.fetchall()


    return render_template('admin/dashboard.html',
                           admin_name=session.get('admin_username'),
                           today_bookings=today_bookings,
                           total_bookings=total_bookings,
                           newsletter_subs=newsletter_subs,
                           recent_reservations=recent_reservations)

def logout():
    session.clear()
    return redirect(url_for('admin.admin_login'))

def view_reservations():
    # This checks if the user is logged in or not
    if 'admin_id' not in session:
        return redirect(url_for('admin.admin_login'))

    # This will get all reservations from the database
    cursor = restaurant_db1.cursor(dictionary=True)
    cursor.execute("""
        SELECT * FROM reservations_restaurant 
        ORDER BY reservation_date DESC, reservation_time DESC
    """)
    all_reservations = cursor.fetchall()

    return render_template('admin/view_reservations.html',
                           reservations=all_reservations)

def manage_menu():
    # This checks if the user is logged in or not
    if 'admin_id' not in session:
        return redirect(url_for('admin.admin_login'))

    # This will get all menu items from the database
    cursor = restaurant_db1.cursor(dictionary=True)
    cursor.execute("SELECT * FROM menu_items ORDER BY category, item_name")
    menu_items = cursor.fetchall()

    return render_template('admin/manage_menu.html', menu_items=menu_items)


def add_menu_item():
    # This checks if the user is logged in or not
    if 'admin_id' not in session:
        return redirect(url_for('admin.admin_login'))

    if request.method == "POST":
        # This gets the form data
        item_name = request.form.get("item_name")
        category = request.form.get("category")
        description = request.form.get("description")
        price = request.form.get("price")

        # This inserts the new menu item into database
        cursor = restaurant_db1.cursor()
        cursor.execute(
            """INSERT INTO menu_items (item_name, category, description, price) 
               VALUES (%s, %s, %s, %s)""",
            (item_name, category, description, price)
        )
        restaurant_db1.commit()

        return redirect(url_for('admin.manage_menu'))

    return render_template('admin/add_menu_item.html')


def edit_menu_item(item_id):
    # This checks if the user is logged in or not
    if 'admin_id' not in session:
        return redirect(url_for('admin.admin_login'))

    cursor = restaurant_db1.cursor(dictionary=True)

    if request.method == "POST":
        # This gets the form data
        item_name = request.form.get("item_name")
        category = request.form.get("category")
        description = request.form.get("description")
        price = request.form.get("price")
        is_available = request.form.get("is_available") == "1"

        # This updates the menu item in database
        cursor.execute(
            """UPDATE menu_items 
               SET item_name=%s, category=%s, description=%s, price=%s, is_available=%s 
               WHERE item_id=%s""",
            (item_name, category, description, price, is_available, item_id)
        )
        restaurant_db1.commit()

        return redirect(url_for('admin.manage_menu'))

    # This gets the current item data
    cursor.execute("SELECT * FROM menu_items WHERE item_id = %s", (item_id,))
    item = cursor.fetchone()

    return render_template('admin/edit_menu_item.html', item=item)


def delete_menu_item(item_id):
    # This checks if the user is logged in or not
    if 'admin_id' not in session:
        return redirect(url_for('admin.admin_login'))

    # This deletes the menu item from database
    cursor = restaurant_db1.cursor()
    cursor.execute("DELETE FROM menu_items WHERE item_id = %s", (item_id,))
    restaurant_db1.commit()

    return redirect(url_for('admin.manage_menu'))