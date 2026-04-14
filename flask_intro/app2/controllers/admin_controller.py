import requests
from flask import render_template, request, redirect, url_for, session, Blueprint
from app2.database import get_db
from werkzeug.security import check_password_hash
from app2 import socketio
from app2.controllers.image_manager_controller import image_manager_controller
from app2.models.category_model import add_category, get_category

def admin_login():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']

        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM admin_restaurant WHERE admin_username = %s", (username,))
        admin = cursor.fetchone()

        if admin and check_password_hash(admin['password_hash'], password):
            session['admin_id'] = admin['admin_id']
            session['admin_username'] = admin['admin_username']
            session['role'] = admin['role']

            cursor.execute(
                "UPDATE admin_restaurant SET last_login = NOW() WHERE admin_id = %s",
                (admin['admin_id'],)
            )
            db.commit()
            cursor.close()
            db.close()
            return redirect(url_for('admin.dashboard'))
        else:
            cursor.close()
            db.close()
            return render_template('staff/login.html', error="Incorrect username or password")
    return render_template('staff/login.html')

def dashboard():
    if 'admin_id' not in session:
        return redirect(url_for('admin.admin_login'))
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT COUNT(*) as count FROM reservations_restaurant WHERE reservation_date = CURDATE()")
    today_bookings = cursor.fetchone()['count']

    cursor.execute("SELECT COUNT(*) as count FROM reservations_restaurant")
    total_bookings = cursor.fetchone()['count']

    cursor.execute("SELECT COUNT(*) as count FROM newsletter_subs WHERE status = 'ACTIVE'")
    newsletter_subs = cursor.fetchone()['count']

    cursor.execute("""
        SELECT * FROM reservations_restaurant 
        ORDER BY reservation_createdate DESC 
        LIMIT 5
    """)
    recent_reservations = cursor.fetchall()
    cursor.close()
    db.close()
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
    if 'admin_id' not in session:
        return redirect(url_for('admin.admin_login'))
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT * FROM reservations_restaurant 
        ORDER BY reservation_date DESC, reservation_time DESC
    """)
    all_reservations = cursor.fetchall()
    cursor.close()
    db.close()

    return render_template('admin/view_reservations.html', reservations=all_reservations)

def manage_menu():
    if 'admin_id' not in session:
        return redirect(url_for('admin.admin_login'))
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM menu_items ORDER BY category, item_name")
    menu_items = cursor.fetchall()
    cursor.close()
    db.close()

    return render_template('admin/manage_menu.html', menu_items=menu_items)

def add_menu_item():
    if 'admin_id' not in session:
        return redirect(url_for('admin.admin_login'))

    if request.method == "POST":
        item_name = request.form.get("item_name")
        category = request.form.get("category")
        description = request.form.get("description")
        price = request.form.get("price")

        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            """INSERT INTO menu_items (item_name, category, description, price) 
               VALUES (%s, %s, %s, %s)""",
            (item_name, category, description, price)
        )
        db.commit()
        cursor.close()
        db.close()

        return redirect(url_for('admin.manage_menu'))
    categories = get_category()
    return render_template('admin/add_menu_item.html', categories=categories)

def edit_menu_item(item_id):
    if 'admin_id' not in session:
        return redirect(url_for('admin.admin_login'))
    db = get_db()
    cursor = db.cursor(dictionary=True)

    if request.method == "POST":
        item_name = request.form.get("item_name")
        category = request.form.get("category")
        description = request.form.get("description")
        price = request.form.get("price")
        is_available = request.form.get("is_available") == "1"
        prep_time = request.form.get("prep_time")

        cursor.execute(
            """UPDATE menu_items 
               SET item_name=%s, category=%s, description=%s, price=%s, is_available=%s, prep_time=%s 
               WHERE item_id=%s""",
            (item_name, category, description, price, is_available, prep_time, item_id)
        )
        db.commit()
        cursor.close()
        db.close()
        return redirect(url_for('admin.manage_menu'))

    cursor.execute("SELECT * FROM menu_items WHERE item_id = %s", (item_id,))
    item = cursor.fetchone()
    cursor.close()
    db.close()
    categories = get_category()
    return render_template('admin/edit_menu_item.html', item=item, categories=categories)

def delete_menu_item(item_id):
    if 'admin_id' not in session:
        return redirect(url_for('admin.admin_login'))
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM menu_items WHERE item_id = %s", (item_id,))
    db.commit()
    cursor.close()
    db.close()
    return redirect(url_for('admin.manage_menu'))


def update_hours():
    if 'admin_id' not in session:
        return redirect(url_for('admin.admin_login'))

    db = get_db()
    cursor = db.cursor(dictionary=True)

    if request.method == "POST":
        address = request.form.get('address')
        lat, lng = None, None
        if address:
            try:
                api_key = ('eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6IjlhM2ZkYzcyOTQ4YzQ3YzE4N'
                           'jlkYWI3MmNhMmYwMjFkIiwiaCI6Im11cm11cjY0In0=')
                geocode_response = requests.get(
                    'https://api.openrouteservice.org/geocode/search',
                    params={'api_key': api_key, 'text': address, 'size': 1}
                )
                geocode_data = geocode_response.json()
                if geocode_data['features']:
                    coords = geocode_data['features'][0]['geometry']['coordinates']
                    lng = coords[0]
                    lat = coords[1]
            except Exception as e:
                print(f"Geocoding error: {e}")

        cursor.execute(
            "UPDATE restaurant_info SET address = %s, latitude = %s, longitude = %s",
            (address, lat, lng)
        )

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
        db.commit()
        cursor.close()
        db.close()
        return redirect(url_for('admin.update_hours'))

    cursor.execute("""
        SELECT * FROM restaurant_info 
        ORDER BY FIELD(day_of_week, 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday')
    """)
    hours = cursor.fetchall()
    cursor.close()
    db.close()
    return render_template('admin/update_hours.html', hours=hours)

def view_analytics():
    if 'admin_id' not in session:
        return redirect(url_for('admin.admin_login'))

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT COUNT(*) FROM reservations_restaurant")
    total_reservations = cursor.fetchone()['COUNT(*)']

    cursor.execute("SELECT COUNT(*) FROM reservations_restaurant WHERE MONTH(reservation_date) = MONTH(NOW())")
    total_monthly_reservations = cursor.fetchone()['COUNT(*)']

    cursor.execute("SELECT AVG(num_of_guests) FROM reservations_restaurant")
    avg_guests = cursor.fetchone()['AVG(num_of_guests)']

    cursor.execute("SELECT table_number, COUNT(*) FROM reservations_restaurant"
                   " GROUP BY table_number ORDER BY COUNT(*) DESC LIMIT 1")
    popular_table = cursor.fetchone()['table_number']

    cursor.execute("""
        SELECT DAYNAME(reservation_date) as day, COUNT(*) as count 
        FROM reservations_restaurant 
        GROUP BY DAYNAME(reservation_date)
        ORDER BY FIELD(day, 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday')
    """)
    bookings_by_day = cursor.fetchall()

    cursor.execute("""
        SELECT HOUR(reservation_time) AS hour, COUNT(*) as count 
        FROM reservations_restaurant 
        GROUP BY HOUR(reservation_time)
        ORDER BY hour
    """)
    bookings_by_time = cursor.fetchall()

    cursor.execute("""
        SELECT MONTHNAME(reservation_date) AS month, COUNT(*) AS count 
        FROM reservations_restaurant 
        WHERE reservation_date >= DATE_SUB(NOW(), INTERVAL 6 MONTH)
        GROUP BY MONTH(reservation_date), YEAR(reservation_date), MONTHNAME(reservation_date)
        ORDER BY YEAR(reservation_date), MONTH(reservation_date)
    """)
    monthly_trend = cursor.fetchall()
    cursor.close()
    db.close()
    return render_template('admin/view_analytics.html',
                           total_reservations=total_reservations,
                           total_monthly_reservations=total_monthly_reservations,
                           total_guests=avg_guests,
                           popular_table=popular_table,
                           bookings_by_day=bookings_by_day,
                           bookings_by_time=bookings_by_time,
                           monthly_trend=monthly_trend)

def view_all_orders():
    if 'admin_id' not in session:
        return redirect(url_for('admin.admin_login'))

    db = get_db()
    cursor = db.cursor(dictionary=True)
    filter_type = request.args.get('filter')

    base_query = """
        SELECT co.*, ca.customer_fullname, ca.customer_email
        FROM customer_orders co
        LEFT JOIN customer_accounts ca ON co.customer_id = ca.customer_id
    """
    params = []
    if filter_type == "today":
        base_query += " WHERE co.order_date = CURDATE()"
    elif filter_type == "delivery":
        base_query += " WHERE co.order_type = 'delivery'"
    elif filter_type in ["pending", "preparing", "ready", "completed", "cancelled"]:
        base_query += " WHERE co.order_status = %s"
        params.append(filter_type)
    base_query += " ORDER BY co.order_date DESC, co.order_time DESC"

    cursor.execute(base_query, params)
    orders = cursor.fetchall()
    cursor.close()
    db.close()
    return render_template('admin/view_all_orders.html', orders=orders)

def view_customer_order(order_id):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM customer_orders WHERE order_id = %s", (order_id,))
    order = cursor.fetchone()

    if not order:
        cursor.close()
        db.close()
        return "Order not found", 404

    customer = None
    if order.get("customer_id"):
        cursor.execute("""
            SELECT customer_fullname, customer_email
            FROM customer_accounts
            WHERE customer_id = %s
        """, (order["customer_id"],))
        customer = cursor.fetchone()
    else:
        customer = {
            "customer_fullname": order.get("guest_fullname"),
            "customer_email": order.get("guest_email")
        }

    cursor.execute("""
        SELECT oi.quantity, oi.item_name, oi.item_price
        FROM order_items oi
        WHERE oi.order_id = %s
    """, (order_id,))
    items = cursor.fetchall()
    cursor.close()
    db.close()
    return render_template('admin/view_customer_order.html',
                           order=order,
                           customer=customer,
                           items=items)

def update_order_status(order_id):
    new_status = request.form.get('status')
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM customer_orders WHERE order_id = %s", (order_id,))
    order = cursor.fetchone()
    estimated_minutes = None

    if order['order_type'] == 'collection':
        cursor.execute("""
            SELECT oi.quantity, mi.prep_time
            FROM order_items oi
            JOIN menu_items mi ON oi.item_name = mi.item_name
            WHERE oi.order_id = %s
        """, (order_id,))
        items = cursor.fetchall()

        total_prep = 10
        for item in items:
            total_prep += item['prep_time'] * item['quantity']
        estimated_minutes = min(total_prep, 60)

    elif order['order_type'] == 'delivery':
        delivery_address = order.get('guest_delivery_address')
        if delivery_address:
            estimated_minutes = get_delivery_minutes(delivery_address)
        else:
            estimated_minutes = 30

    cursor.execute(
        "UPDATE customer_orders SET order_status = %s, estimated_minutes = %s WHERE order_id = %s",
        (new_status, estimated_minutes, order_id)
    )
    db.commit()
    cursor.close()
    db.close()

    socketio.emit('order_status_update', {
        'order_id': order_id,
        'new_status': new_status,
        'estimated_minutes': estimated_minutes
    }, room=f'order_{order_id}')

    socketio.emit('kitchen_update', {
        'order_id': order_id,
        'new_status': new_status
    }, room='kitchen')
    return redirect(url_for('admin.view_all_orders'))

def get_delivery_minutes(delivery_address):
    api_key = ('eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6IjlhM2ZkYzcyOTQ4YzQ3YzE4'
               'NjlkYWI3MmNhMmYwMjFkIiwiaCI6Im11cm11cjY0In0=')

    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT latitude, longitude FROM restaurant_info WHERE latitude IS NOT NULL LIMIT 1")
    restaurant = cursor.fetchone()
    cursor.close()
    db.close()

    if not restaurant:
        return 30

    restaurant_lat = float(restaurant['latitude'])
    restaurant_lng = float(restaurant['longitude'])

    try:
        geocode_response = requests.get(
            'https://api.openrouteservice.org/geocode/search',
            params={'api_key': api_key, 'text': delivery_address, 'size': 1}
        )
        geocode_data = geocode_response.json()

        if not geocode_data['features']:
            return 30

        coords = geocode_data['features'][0]['geometry']['coordinates']
        customer_lng = coords[0]
        customer_lat = coords[1]

        directions_response = requests.post(
            'https://api.openrouteservice.org/v2/directions/driving-car',
            json={'coordinates': [[restaurant_lng, restaurant_lat], [customer_lng, customer_lat]]},
            headers={'Authorization': api_key}
        )
        directions_data = directions_response.json()

        duration_seconds = directions_data['routes'][0]['summary']['duration']
        duration_minutes = int(duration_seconds / 60)
        return duration_minutes + 10

    except Exception as e:
        print(f"OpenRouteService error: {e}")
        return 30

def image_manager():
    context = image_manager_controller()
    return render_template("admin/image_manager.html", **context)

def manage_categories():
    if 'admin_id' not in session:
        return redirect(url_for('admin.admin_login'))
    if request.method == 'POST':
        name = request.form.get("category_name")
        if name:
            add_category(name)
        return redirect(url_for('admin.manage_categories'))
    categories = get_category()
    return render_template('admin/manage_categories.html', categories=categories)

def delete_category(category_id):
    if 'admin_id' not in session:
        return redirect(url_for('admin.admin_login'))
    from app2.models.category_model import delete_category as del_cat
    del_cat(category_id)
    return redirect(url_for('admin.manage_categories'))