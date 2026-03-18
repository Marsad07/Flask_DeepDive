from flask import render_template, request, redirect, url_for, session
from app2.database import restaurant_db1
from werkzeug.security import check_password_hash

def admin_login():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']

        # This checks for the users credentials
        cursor = restaurant_db1.cursor(dictionary=True)
        cursor.execute("SELECT * FROM admin_restaurant WHERE admin_username = %s", (username,)        )
        admin = cursor.fetchone()

        # This verifies the password
        if admin and check_password_hash(admin['password_hash'], password):
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
    cursor.execute("SELECT COUNT(*) as count FROM newsletter_subs WHERE status = 'ACTIVE'")
    newsletter_subs = cursor.fetchone()['count']

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

def update_hours():
    if 'admin_id' not in session:
        return redirect(url_for('admin.admin_login'))
    cursor = restaurant_db1.cursor(dictionary=True)

    if request.method == "POST":
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        for day in days:
            day_lower = day.lower()
            open_time = request.form.get(f"{day_lower}_open")
            close_time = request.form.get(f"{day_lower}_close")
            is_closed = 1 if request.form.get(f"{day_lower}_closed") else 0

            cursor.execute(
                "UPDATE restaurant_info SET opening_time=%s, closing_time=%s, is_closed=%s WHERE day_of_week=%s",
                (open_time, close_time, is_closed, day)
            )
        restaurant_db1.commit()
        return redirect(url_for('admin.update_hours'))

    if request.method == "GET":
        cursor.execute("SELECT * FROM restaurant_info ORDER BY FIELD(day_of_week,"
                       " 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday')")
        hours = cursor.fetchall()

        return render_template('admin/update_hours.html', hours=hours)

def view_analytics():
    # This checks if the user is logged in or not
    if 'admin_id' not in session:
        return redirect(url_for('admin.admin_login'))

    cursor = restaurant_db1.cursor(dictionary=True)

    # This gets the total number of reservations
    cursor.execute("SELECT COUNT(*) FROM reservations_restaurant")
    result = cursor.fetchone()
    total_reservations = result['COUNT(*)']

    # This gets the total reservations for this month
    cursor.execute("SELECT COUNT(*) FROM reservations_restaurant WHERE MONTH(reservation_date) "
                   "= MONTH(NOW())")
    result = cursor.fetchone()
    total_monthly_reservations = result['COUNT(*)']

    # This gets the average number of guests per booking
    cursor.execute("SELECT AVG(num_of_guests) FROM reservations_restaurant")
    result = cursor.fetchone()
    avg_guests = result['AVG(num_of_guests)']

    # This gets the most popular table number
    cursor.execute("SELECT table_number, COUNT(*) FROM reservations_restaurant "
                   "GROUP BY table_number ORDER BY COUNT(*) DESC LIMIT 1 ")
    result = cursor.fetchone()
    popular_table = result['table_number']

    # This gets booking counts grouped by day of week
    cursor.execute("""
        SELECT DAYNAME(reservation_date) as day, COUNT(*) as count 
        FROM reservations_restaurant 
        GROUP BY DAYNAME(reservation_date)
        ORDER BY FIELD(day, 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday')
    """)
    bookings_by_day = cursor.fetchall()

    # This gets booking counts grouped by hour of day
    cursor.execute("""
        SELECT HOUR(reservation_time) AS hour, COUNT(*) as count 
        FROM reservations_restaurant 
        GROUP BY HOUR(reservation_time)
        ORDER BY hour
    """)
    bookings_by_time = cursor.fetchall()

    # This gets booking counts for the last 6 months
    cursor.execute("""
        SELECT MONTHNAME(reservation_date) AS month, COUNT(*) AS count 
        FROM reservations_restaurant 
        WHERE reservation_date >= DATE_SUB(NOW(), INTERVAL 6 MONTH)
        GROUP BY MONTH(reservation_date), YEAR(reservation_date), MONTHNAME(reservation_date)
        ORDER BY YEAR(reservation_date), MONTH(reservation_date)
    """)
    monthly_trend = cursor.fetchall()
    return render_template('admin/view_analytics.html',
                           total_reservations=total_reservations,
                           total_monthly_reservations=total_monthly_reservations,
                           total_guests=avg_guests,
                           popular_table=popular_table,
                           bookings_by_day=bookings_by_day,
                           bookings_by_time=bookings_by_time,
                           monthly_trend=monthly_trend)