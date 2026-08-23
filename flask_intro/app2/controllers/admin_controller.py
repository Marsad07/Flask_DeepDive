import requests
from flask import render_template, request, redirect, url_for, session, Blueprint, Response, current_app, flash
from app2.database import get_db
from werkzeug.security import check_password_hash, generate_password_hash
from app2 import socketio
from app2.controllers.image_manager_controller import image_manager_controller
from app2.models.category_model import add_category, get_category
import os
from werkzeug.utils import secure_filename
from app2.models.homepage_model import (get_branding, update_branding, get_all_reviews,
                                         update_review, add_review, delete_review,
                                         get_dishes, update_dish)
from app2.models.themeSettings_model import get_theme, save_theme
from app2.models.menu_model import MenuItem
from app2.models.order_model import Order
from app2.models.staff_model import StaffAccount
from app2.models.social_link_model import SocialLink
from app2.models.table_model import RestaurantTable

GOOGLE_FONTS = [
    'Lato', 'Roboto', 'Open Sans', 'Montserrat', 'Raleway',
    'Nunito', 'Poppins', 'Inter', 'Source Sans Pro', 'Ubuntu'
]

HEADING_FONTS = [
    'Playfair Display', 'Merriweather', 'Lora', 'Cormorant Garamond',
    'EB Garamond', 'Libre Baskerville', 'Crimson Text', 'Bitter'
]

def admin_login():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']

        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM admin_restaurant WHERE admin_username = %s", (username,))
        admin = cursor.fetchone()

        if admin and check_password_hash(admin['password_hash'], password):
            session.permanent = True
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
    cursor.execute(
        "SELECT COUNT(*) as count FROM reservations_restaurant "
        "WHERE reservation_date = CURDATE()"
    )
    today_bookings = cursor.fetchone()['count']

    cursor.execute("SELECT COUNT(*) as count FROM reservations_restaurant")
    total_bookings = cursor.fetchone()['count']

    cursor.execute(
        "SELECT COUNT(*) as count FROM newsletter_subs WHERE status = 'ACTIVE'"
    )
    newsletter_subs = cursor.fetchone()['count']

    cursor.execute(
        "SELECT COUNT(*) as count FROM customer_orders "
        "WHERE DATE(order_date) = CURDATE()"
    )
    today_orders = cursor.fetchone()['count']

    cursor.execute(
        "SELECT COALESCE(SUM(total_price), 0) as revenue FROM customer_orders "
        "WHERE DATE(order_date) = CURDATE() AND order_status <> 'cancelled'"
    )
    today_revenue = cursor.fetchone()['revenue']

    cursor.execute(
        "SELECT COUNT(*) as count FROM customer_orders "
        "WHERE order_status IN ('pending', 'confirmed')"
    )
    pending_orders = cursor.fetchone()['count']

    cursor.execute("""
        SELECT * FROM reservations_restaurant
        ORDER BY reservation_createdate DESC
        LIMIT 4
    """)
    recent_reservations = cursor.fetchall()

    cursor.execute("""
        SELECT order_id, order_type, order_status, total_price, order_date
        FROM customer_orders
        ORDER BY order_date DESC, order_time DESC
        LIMIT 4
    """)
    recent_orders = cursor.fetchall()

    cursor.execute("""
        SELECT s.staff_id, s.full_name, s.is_available, s.is_active,
               o.order_id as current_order
        FROM staff_accounts s
        LEFT JOIN customer_orders o
            ON o.assigned_driver_id = s.staff_id
            AND o.order_status NOT IN ('completed', 'cancelled')
        WHERE s.role = 'driver'
        ORDER BY s.is_active DESC, s.is_available DESC
        LIMIT 4
    """)
    drivers = cursor.fetchall()

    cursor.close()
    db.close()
    return render_template('admin/dashboard.html',
                           admin_name=session.get('admin_username'),
                           today_bookings=today_bookings,
                           total_bookings=total_bookings,
                           newsletter_subs=newsletter_subs,
                           today_orders=today_orders,
                           today_revenue=today_revenue,
                           pending_orders=pending_orders,
                           recent_reservations=recent_reservations,
                           recent_orders=recent_orders,
                           drivers=drivers)

def logout():
    session.clear()
    return redirect(url_for('admin.admin_login'))

def view_reservations():
    if 'admin_id' not in session:
        return redirect(url_for('admin.admin_login'))

    db = get_db()
    cursor = db.cursor(dictionary=True)
    filter_type = request.args.get('filter', '')
    search      = request.args.get('search', '').strip()

    base_query = "SELECT * FROM reservations_restaurant"
    conditions = []
    params     = []

    if filter_type == 'today':
        conditions.append("reservation_date = CURDATE()")
    elif filter_type == 'upcoming':
        conditions.append("reservation_date >= CURDATE()")
    elif filter_type == 'past':
        conditions.append("reservation_date < CURDATE()")
    elif filter_type in ('Confirmed', 'Cancelled', 'Pending'):
        conditions.append("reservation_status = %s")
        params.append(filter_type)

    if search:
        conditions.append("""
            (customer_fullname LIKE %s
             OR customer_email LIKE %s
             OR customer_phonenum LIKE %s)
        """)
        like = f"%{search}%"
        params.extend([like, like, like])

    if conditions:
        base_query += " WHERE " + " AND ".join(conditions)

    base_query += " ORDER BY reservation_date DESC, reservation_time DESC"
    cursor.execute(base_query, params)
    all_reservations = cursor.fetchall()

    # Summary counts for stat cards
    cursor.execute("SELECT COUNT(*) AS c FROM reservations_restaurant WHERE reservation_date = CURDATE()")
    today_count = cursor.fetchone()['c']

    cursor.execute("SELECT COUNT(*) AS c FROM reservations_restaurant "
                   "WHERE reservation_date >= CURDATE() AND reservation_status <> 'Cancelled'")
    upcoming_count = cursor.fetchone()['c']

    cursor.execute("SELECT COUNT(*) AS c FROM reservations_restaurant WHERE reservation_status = 'Cancelled'")
    cancelled_count = cursor.fetchone()['c']

    cursor.execute("SELECT COUNT(*) AS c FROM reservations_restaurant")
    total_count = cursor.fetchone()['c']

    cursor.close()
    db.close()
    return render_template(
        'admin/view_reservations.html',
        reservations=all_reservations,
        filter_type=filter_type,
        search=search,
        today_count=today_count,
        upcoming_count=upcoming_count,
        cancelled_count=cancelled_count,
        total_count=total_count
    )

def manage_menu():
    if 'admin_id' not in session:
        return redirect(url_for('admin.admin_login'))

    # Uses MenuItem model instead of raw SQL
    menu_items = MenuItem.query.order_by(MenuItem.category, MenuItem.item_name).all()
    return render_template('admin/manage_menu.html', menu_items=menu_items)

def add_menu_item():
    if 'admin_id' not in session:
        return redirect(url_for('admin.admin_login'))

    if request.method == "POST":
        # Uses MenuItem model to create a new item
        MenuItem.create(
            item_name=request.form.get("item_name"),
            category=request.form.get("category"),
            description=request.form.get("description"),
            price=request.form.get("price")
        )
        return redirect(url_for('admin.manage_menu'))

    categories = get_category()
    return render_template('admin/add_menu_item.html', categories=categories)

def edit_menu_item(item_id):
    if 'admin_id' not in session:
        return redirect(url_for('admin.admin_login'))

    # Uses MenuItem model to get and update the item
    item = MenuItem.get_by_id(item_id)
    if not item:
        return redirect(url_for('admin.manage_menu'))

    if request.method == "POST":
        item.update(
            item_name=request.form.get("item_name"),
            category=request.form.get("category"),
            description=request.form.get("description"),
            price=request.form.get("price"),
            is_available=request.form.get("is_available") == "1"
        )
        return redirect(url_for('admin.manage_menu'))

    categories = get_category()
    return render_template('admin/edit_menu_item.html', item=item, categories=categories)

def delete_menu_item(item_id):
    if 'admin_id' not in session:
        return redirect(url_for('admin.admin_login'))

    # Uses MenuItem model to delete the item
    item = MenuItem.get_by_id(item_id)
    if item:
        item.delete()
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
                api_key = current_app.config['ORS_API_KEY']
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

    # --- Reservations stats ---
    cursor.execute("SELECT COUNT(*) FROM reservations_restaurant")
    total_reservations = cursor.fetchone()['COUNT(*)']

    cursor.execute("SELECT COUNT(*) FROM reservations_restaurant WHERE MONTH(reservation_date) = MONTH(NOW())")
    total_monthly_reservations = cursor.fetchone()['COUNT(*)']

    cursor.execute("SELECT AVG(num_of_guests) FROM reservations_restaurant")
    avg_guests = cursor.fetchone()['AVG(num_of_guests)']

    cursor.execute("SELECT table_number, COUNT(*) FROM reservations_restaurant"
                   " GROUP BY table_number ORDER BY COUNT(*) DESC LIMIT 1")
    row = cursor.fetchone()
    popular_table = row['table_number'] if row else '—'

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

    # --- Order stats --- uses Order model methods where possible
    cursor.execute("SELECT COUNT(*) AS c FROM customer_orders")
    row = cursor.fetchone()
    total_orders = row['c'] if row else 0

    cursor.execute("""
        SELECT COUNT(*) AS c FROM customer_orders 
        WHERE MONTH(order_date) = MONTH(NOW()) AND YEAR(order_date) = YEAR(NOW())
    """)
    row = cursor.fetchone()
    total_monthly_orders = row['c'] if row else 0

    cursor.execute("""
        SELECT COALESCE(SUM(total_price), 0) AS t FROM customer_orders 
        WHERE order_status != 'cancelled'
    """)
    total_revenue = float(cursor.fetchone()['t'])

    cursor.execute("""
        SELECT COALESCE(SUM(total_price), 0) AS t FROM customer_orders 
        WHERE order_status != 'cancelled'
        AND MONTH(order_date) = MONTH(NOW()) AND YEAR(order_date) = YEAR(NOW())
    """)
    monthly_revenue = float(cursor.fetchone()['t'])

    cursor.execute("""
        SELECT oi.item_name, SUM(oi.quantity) AS total_qty
        FROM order_items oi
        JOIN customer_orders co ON oi.order_id = co.order_id
        WHERE co.order_status != 'cancelled'
        GROUP BY oi.item_name
        ORDER BY total_qty DESC
        LIMIT 10
    """)
    top_items_qty = cursor.fetchall()

    cursor.execute("""
        SELECT oi.item_name, ROUND(SUM(oi.quantity * oi.item_price), 2) AS total_revenue
        FROM order_items oi
        JOIN customer_orders co ON oi.order_id = co.order_id
        WHERE co.order_status != 'cancelled'
        GROUP BY oi.item_name
        ORDER BY total_revenue DESC
        LIMIT 10
    """)
    top_items_revenue = cursor.fetchall()

    cursor.execute("""
        SELECT MONTHNAME(order_date) AS month,
               ROUND(SUM(total_price), 2) AS revenue,
               COUNT(*) AS order_count
        FROM customer_orders
        WHERE order_status != 'cancelled'
        AND order_date >= DATE_SUB(NOW(), INTERVAL 6 MONTH)
        GROUP BY MONTH(order_date), YEAR(order_date), MONTHNAME(order_date)
        ORDER BY YEAR(order_date), MONTH(order_date)
    """)
    revenue_trend = cursor.fetchall()

    cursor.execute("""
        SELECT order_type, COUNT(*) AS count
        FROM customer_orders
        WHERE order_status != 'cancelled'
        GROUP BY order_type
    """)
    orders_by_type = cursor.fetchall()

    cursor.close()
    db.close()
    return render_template('admin/view_analytics.html',
                           total_reservations=total_reservations,
                           total_monthly_reservations=total_monthly_reservations,
                           total_guests=avg_guests,
                           popular_table=popular_table,
                           bookings_by_day=bookings_by_day,
                           bookings_by_time=bookings_by_time,
                           monthly_trend=monthly_trend,
                           total_orders=total_orders,
                           total_monthly_orders=total_monthly_orders,
                           total_revenue=total_revenue,
                           monthly_revenue=monthly_revenue,
                           top_items_qty=top_items_qty,
                           top_items_revenue=top_items_revenue,
                           revenue_trend=revenue_trend,
                           orders_by_type=orders_by_type)

def view_all_orders():
    if 'admin_id' not in session:
        return redirect(url_for('admin.admin_login'))

    db = get_db()
    cursor = db.cursor(dictionary=True)
    filter_type = request.args.get('filter', '')
    search      = request.args.get('search', '').strip()

    base_query = """
        SELECT co.*, ca.customer_fullname, ca.customer_email
        FROM customer_orders co
        LEFT JOIN customer_accounts ca ON co.customer_id = ca.customer_id
    """
    conditions = []
    params     = []

    # Status / type filters
    if filter_type == 'today':
        conditions.append("co.order_date = CURDATE()")
    elif filter_type == 'delivery':
        conditions.append("co.order_type = 'delivery'")
    elif filter_type == 'collection':
        conditions.append("co.order_type = 'collection'")
    elif filter_type in ('pending', 'confirmed', 'preparing', 'ready', 'completed', 'cancelled'):
        conditions.append("co.order_status = %s")
        params.append(filter_type)

    if search:
        conditions.append("""
            (co.guest_fullname LIKE %s
             OR co.guest_email LIKE %s
             OR ca.customer_fullname LIKE %s
             OR ca.customer_email LIKE %s
             OR CAST(co.order_id AS CHAR) LIKE %s)
        """)
        like = f"%{search}%"
        params.extend([like, like, like, like, like])

    if conditions:
        base_query += " WHERE " + " AND ".join(conditions)

    base_query += " ORDER BY co.order_date DESC, co.order_time DESC"

    cursor.execute(base_query, params)
    orders = cursor.fetchall()

    # Summary counts for stat cards
    cursor.execute("SELECT COUNT(*) AS c FROM customer_orders WHERE order_date = CURDATE()")
    today_count = cursor.fetchone()['c']

    cursor.execute("SELECT COUNT(*) AS c FROM customer_orders"
                   " WHERE order_status = 'cancelled' AND order_date = CURDATE()")
    active_count = cursor.fetchone()['c']

    cursor.execute("SELECT COALESCE(SUM(total_price),0) AS t FROM customer_orders WHERE order_date = CURDATE()")
    today_revenue = cursor.fetchone()['t']

    cursor.execute("SELECT COUNT(*) AS c FROM customer_orders"
                   " WHERE order_status = 'cancelled' AND order_date = CURDATE()")
    cancelled_today = cursor.fetchone()['c']

    cursor.close()
    db.close()
    return render_template(
        'admin/view_all_orders.html',
        orders=orders,
        filter_type=filter_type,
        search=search,
        today_count=today_count,
        active_count=active_count,
        today_revenue=today_revenue,
        cancelled_today=cancelled_today
    )

def view_customer_order(order_id):
    # Uses Order model to get the order
    order = Order.get_by_id(order_id)
    if not order:
        return "Order not found", 404

    db = get_db()
    cursor = db.cursor(dictionary=True)

    customer = None
    if order.customer_id:
        cursor.execute("""
            SELECT customer_fullname, customer_email
            FROM customer_accounts
            WHERE customer_id = %s
        """, (order.customer_id,))
        customer = cursor.fetchone()
    else:
        customer = {
            "customer_fullname": order.guest_fullname,
            "customer_email": order.guest_email
        }

    cursor.execute("""
        SELECT oi.quantity, oi.item_name, oi.item_price
        FROM order_items oi
        WHERE oi.order_id = %s
    """, (order_id,))
    items = cursor.fetchall()

    # Uses StaffAccount model to get active drivers
    drivers = StaffAccount.get_drivers()

    cursor.close()
    db.close()
    return render_template('admin/view_customer_order.html',
                           order=order,
                           customer=customer,
                           items=items,
                           drivers=drivers)

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
    api_key = current_app.config['ORS_API_KEY']

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
    if isinstance(context, Response):
        return context
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

def manage_homepage():
    if 'admin_id' not in session:
        return redirect(url_for('admin.admin_login'))

    branding = get_branding()
    reviews = get_all_reviews()
    dishes = get_dishes()

    return render_template('admin/manage_homepage.html',
                           branding=branding,
                           reviews=reviews,
                           dishes=dishes)

def update_branding_settings():
    if 'admin_id' not in session:
        return redirect(url_for('admin.admin_login'))

    use_logo = request.form.get('use_logo') == 'true'
    restaurant_name = request.form.get('restaurant_name')
    restaurant_motto = request.form.get('restaurant_motto')
    logo_path = get_branding().get('logo_path')

    file = request.files.get('logo_file')
    if file and file.filename:
        filename = secure_filename(file.filename)
        upload_folder = os.path.join(current_app.root_path, 'static', 'imgs')
        file.save(os.path.join(upload_folder, filename))
        logo_path = f"/static/imgs/{filename}"

    update_branding(use_logo, logo_path, restaurant_name, restaurant_motto)
    return redirect(url_for('admin.manage_homepage'))

def update_review_item():
    if 'admin_id' not in session:
        return redirect(url_for('admin.admin_login'))

    review_id = request.form.get('review_id')
    reviewer_name = request.form.get('reviewer_name')
    review_text = request.form.get('review_text')
    rating = request.form.get('rating')
    is_visible = request.form.get('is_visible') == '1'

    update_review(review_id, reviewer_name, review_text, rating, is_visible)
    return redirect(url_for('admin.manage_homepage'))

def add_review_item():
    if 'admin_id' not in session:
        return redirect(url_for('admin.admin_login'))

    reviewer_name = request.form.get('reviewer_name')
    review_text = request.form.get('review_text')
    rating = request.form.get('rating', 5)

    add_review(reviewer_name, review_text, rating)
    return redirect(url_for('admin.manage_homepage'))

def delete_review_item(review_id):
    if 'admin_id' not in session:
        return redirect(url_for('admin.admin_login'))
    delete_review(review_id)
    return redirect(url_for('admin.manage_homepage'))

def update_dish_item():
    if 'admin_id' not in session:
        return redirect(url_for('admin.admin_login'))

    dish_key = request.form.get('dish_key')
    dish_name = request.form.get('dish_name')
    dish_description = request.form.get('dish_description')

    update_dish(dish_key, dish_name, dish_description)
    return redirect(url_for('admin.manage_homepage'))

def assign_driver(order_id):
    driver_id = request.form.get("driver_id")

    # Uses Order model to update assigned driver
    order = Order.get_by_id(order_id)
    if order:
        order.update(assigned_driver_id=driver_id)

    return redirect(url_for('admin.view_customer_order', order_id=order_id))

def offer_driver(order_id):
    driver_id = int(request.form.get("driver_id"))
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT driver_offer_id, driver_offer_status
        FROM customer_orders
        WHERE order_id = %s
    """, (order_id,))
    existing = cursor.fetchone()
    if existing["driver_offer_id"] == driver_id:
        status = existing["driver_offer_status"]
        messages = {
            "pending":  "This driver has already been offered this order and has not responded yet.",
            "declined": "This driver has already declined this order.",
            "accepted": "This driver has already accepted this order."
        }
        if status in messages:
            cursor.close()
            db.close()
            flash(messages[status], "driver_warning")
            return redirect(url_for('admin.view_customer_order', order_id=order_id))

    cursor.execute("""
        SELECT 
            customer_id,
            guest_fullname,
            guest_delivery_address,
            total_price
        FROM customer_orders
        WHERE order_id = %s
    """, (order_id,))
    order = cursor.fetchone()
    customer_name = None
    if order["customer_id"]:
        cursor.execute("""
            SELECT customer_fullname 
            FROM customer_accounts 
            WHERE customer_id = %s
        """, (order["customer_id"],))
        cust = cursor.fetchone()
        if cust:
            customer_name = cust["customer_fullname"]

    if not customer_name:
        customer_name = order["guest_fullname"]

    address     = order["guest_delivery_address"]
    total_price = order["total_price"]

    cursor.execute("""
        UPDATE customer_orders
        SET assigned_driver_id = NULL,
            driver_offer_id = %s,
            driver_offer_status = 'pending',
            order_status = 'pending'
        WHERE order_id = %s
    """, (driver_id, order_id))
    db.commit()
    cursor.close()
    db.close()
    print(f"DEBUG emitting to room: driver_{driver_id}")
    socketio.emit("driver_offer", {
        "order_id":      order_id,
        "customer_name": customer_name,
        "address":       address,
        "total_price":   float(total_price),
    }, room=f"driver_{driver_id}")

    return redirect(url_for('admin.view_customer_order', order_id=order_id))

def manage_contact():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT * FROM restaurant_contact LIMIT 1")
    contact = cursor.fetchone()

    if request.method == "POST":
        address = request.form["address"]
        phone = request.form["phone"]
        email = request.form["email"]

        if contact:
            cursor.execute("""
                UPDATE restaurant_contact
                SET address=%s, phonenumber=%s, email=%s
                WHERE id=%s
            """, (address, phone, email, contact["id"]))
        else:
            cursor.execute("""
                INSERT INTO restaurant_contact (address, phonenumber, email)
                VALUES (%s, %s, %s)
            """, (address, phone, email))

        db.commit()

    return render_template("admin/edit_contact_details.html", info=contact)

def manage_social_links():
    if 'admin_id' not in session:
        return redirect(url_for('admin.admin_login'))

    # Uses SocialLink model to get all links
    links = SocialLink.query.order_by(SocialLink.display_order).all()
    return render_template("admin/social_links.html", links=links)

def add_social_link():
    if 'admin_id' not in session:
        return redirect(url_for('admin.admin_login'))

    # Uses SocialLink model to create a new link
    SocialLink.create(
        platform=request.form.get('platform'),
        url=request.form.get('url'),
        icon_class=request.form.get('icon_class'),
        display_order=request.form.get('display_order', 0)
    )
    flash('Social link added', 'success')
    return redirect(url_for('admin.manage_social_links'))

def edit_social_link(link_id):
    if 'admin_id' not in session:
        return redirect(url_for('admin.admin_login'))

    # Uses SocialLink model to update the link
    link = SocialLink.get_by_id(link_id)
    if link:
        link.update(
            url=request.form.get('url'),
            icon_class=request.form.get('icon_class'),
            platform=request.form.get('platform'),
            display_order=request.form.get('display_order', 0),
            is_active=request.form.get('is_active', 1)
        )
    flash('Social link updated', 'success')
    return redirect(url_for('admin.manage_social_links'))

def delete_social_link(link_id):
    if 'admin_id' not in session:
        return redirect(url_for('admin.admin_login'))

    # Uses SocialLink model to delete the link
    link = SocialLink.get_by_id(link_id)
    if link:
        link.delete()
    flash('Social link removed', 'success')
    return redirect(url_for('admin.manage_social_links'))

def manage_about():
    if 'admin_id' not in session:
        return redirect(url_for('admin.admin_login'))

    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM about_us ORDER BY display_order ASC")
    sections = cursor.fetchall()
    cursor.close()
    db.close()
    return render_template('admin/manage_about.html', sections=sections)

def update_about_section(section_id):
    if 'admin_id' not in session:
        return redirect(url_for('admin.admin_login'))

    heading = request.form.get('heading')
    content = request.form.get('content')

    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        UPDATE about_us SET heading = %s, content = %s 
        WHERE id = %s
    """, (heading, content, section_id))
    db.commit()
    cursor.close()
    db.close()
    flash('Section updated', 'success')
    return redirect(url_for('admin.manage_about'))

def add_about_section():
    if 'admin_id' not in session:
        return redirect(url_for('admin.admin_login'))

    heading = request.form.get('heading')
    content = request.form.get('content')

    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT MAX(display_order) as max_order FROM about_us
    """)
    result = cursor.fetchone()
    next_order = (result['max_order'] or 0) + 1
    section_key = f"section_{next_order}"

    cursor.execute("""
        INSERT INTO about_us (section_key, heading, content, display_order)
        VALUES (%s, %s, %s, %s)
    """, (section_key, heading, content, next_order))
    db.commit()
    cursor.close()
    db.close()
    flash('Section added', 'success')
    return redirect(url_for('admin.manage_about'))

def delete_about_section(section_id):
    if 'admin_id' not in session:
        return redirect(url_for('admin.admin_login'))

    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("DELETE FROM about_us WHERE id = %s", (section_id,))
    db.commit()
    cursor.close()
    db.close()
    flash('Section deleted', 'success')
    return redirect(url_for('admin.manage_about'))

def manage_drivers():
    if 'admin_id' not in session:
        return redirect(url_for('admin.admin_login'))

    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT 
            s.staff_id, s.full_name, s.staff_username, 
            s.is_available, s.is_active,
            o.order_id as current_order_id,
            o.order_status as current_order_status
        FROM staff_accounts s
        LEFT JOIN customer_orders o 
            ON o.assigned_driver_id = s.staff_id 
            AND o.order_status NOT IN ('completed', 'cancelled')
        WHERE s.role = 'driver'
        ORDER BY s.is_available DESC, s.full_name ASC
    """)
    drivers = cursor.fetchall()
    cursor.close()
    db.close()
    return render_template('admin/manage_drivers.html', drivers=drivers)

def toggle_driver_active(staff_id):
    if 'admin_id' not in session:
        return redirect(url_for('admin.admin_login'))

    # Uses StaffAccount model to toggle active status
    staff = StaffAccount.get_by_id(staff_id)
    if staff and staff.role == 'driver':
        if staff.is_active:
            staff.disable()
        else:
            staff.enable()
    flash('Driver status updated', 'success')
    return redirect(url_for('admin.manage_drivers'))

def manage_tables():
    if 'admin_id' not in session:
        return redirect(url_for('admin.admin_login'))

    # Uses RestaurantTable model to get all tables
    tables = RestaurantTable.query.order_by(RestaurantTable.table_number).all()
    return render_template('admin/manage_tables.html', tables=tables)

def save_table_positions():
    if 'admin_id' not in session:
        return redirect(url_for('admin.admin_login'))

    import json
    positions = request.json.get('positions', [])

    # Uses RestaurantTable model to update positions
    for pos in positions:
        table = RestaurantTable.get_by_id(pos['id'])
        if table:
            table.update(pos_x=pos['x'], pos_y=pos['y'])

    socketio.emit('tables_updated', positions)
    return {'success': True}

def add_table():
    if 'admin_id' not in session:
        return redirect(url_for('admin.admin_login'))

    # Uses RestaurantTable model to create a new table
    RestaurantTable.create(
        table_number=request.form.get('table_number'),
        seats=request.form.get('seats'),
        location=request.form.get('location'),
        shape=request.form.get('shape'),
        pos_x=50,
        pos_y=50
    )
    flash('Table added', 'success')
    return redirect(url_for('admin.manage_tables'))

def delete_table(table_id):
    if 'admin_id' not in session:
        return redirect(url_for('admin.admin_login'))

    # Uses RestaurantTable model to delete the table
    table = RestaurantTable.get_by_id(table_id)
    if table:
        table.delete()
    flash('Table removed', 'success')
    return redirect(url_for('admin.manage_tables'))

def update_table(table_id):
    if 'admin_id' not in session:
        return redirect(url_for('admin.admin_login'))

    # Uses RestaurantTable model to update the table
    table = RestaurantTable.get_by_id(table_id)
    if table:
        table.update(
            seats=request.form.get('seats'),
            location=request.form.get('location'),
            shape=request.form.get('shape'),
            is_active=request.form.get('is_active', 1)
        )
    flash('Table updated', 'success')
    return redirect(url_for('admin.manage_tables'))

def manage_staff():
    if 'admin_id' not in session:
        return redirect(url_for('staff.staff_login'))

    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM staff_accounts ORDER BY created_at DESC")
    staff_list = cursor.fetchall()
    cursor.close()
    db.close()
    return render_template("admin/manage_staff.html", staff_list=staff_list)

def create_staff():
    if 'admin_id' not in session:
        return redirect(url_for('staff.staff_login'))

    if request.method == "POST":
        full_name = request.form.get("full_name")
        username = request.form.get("username")
        email = request.form.get("email")
        password = generate_password_hash(request.form.get("password"))
        role = request.form.get("role")

        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            INSERT INTO staff_accounts (full_name, staff_username, email, password_hash, role, is_active, is_available)
            VALUES (%s, %s, %s, %s, %s, 1, 1)
        """, (full_name, username, email, password, role))
        db.commit()
        cursor.close()
        db.close()
        return redirect(url_for('admin.manage_staff'))

    return render_template("admin/create_staff.html")

def edit_staff(staff_id):
    if 'admin_id' not in session:
        return redirect(url_for('staff.staff_login'))

    db = get_db()
    cursor = db.cursor(dictionary=True)

    if request.method == "POST":
        full_name = request.form.get("full_name")
        email = request.form.get("email")
        role = request.form.get("role")
        is_active = 1 if request.form.get("is_active") else 0
        is_available = 1 if request.form.get("is_available") else 0

        cursor.execute("""
            UPDATE staff_accounts
            SET full_name=%s, email=%s, role=%s, is_active=%s, is_available=%s
            WHERE staff_id=%s
        """, (full_name, email, role, is_active, is_available, staff_id))
        new_password = request.form.get("password")
        if new_password:
            hashed = generate_password_hash(new_password)
            cursor.execute("UPDATE staff_accounts SET password_hash=%s WHERE staff_id=%s",
                           (hashed, staff_id))

        db.commit()
        cursor.close()
        db.close()
        return redirect(url_for('admin.manage_staff'))

    cursor.execute("SELECT * FROM staff_accounts WHERE staff_id=%s", (staff_id,))
    staff = cursor.fetchone()
    cursor.close()
    db.close()

    return render_template("admin/edit_staff.html", staff=staff)

def disable_staff(staff_id):
    if 'admin_id' not in session:
        return redirect(url_for('staff.staff_login'))

    # Uses StaffAccount model to disable the staff member
    staff = StaffAccount.get_by_id(staff_id)
    if staff:
        staff.disable()
    return redirect(url_for('admin.manage_staff'))

def driver_details(driver_id):
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT * FROM staff_accounts
        WHERE staff_id = %s
    """, (driver_id,))
    driver = cursor.fetchone()

    cursor.execute("""
        SELECT * FROM customer_orders
        WHERE assigned_driver_id = %s
        ORDER BY order_id DESC
    """, (driver_id,))
    orders = cursor.fetchall()

    cursor.close()
    return render_template("admin/driver_details.html", driver=driver, orders=orders)

def update_footer_about():
    if request.method == "POST":
        footer_about = request.form['footer_about']

        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            "UPDATE restaurant_branding SET footer_about = %s",
            (footer_about,)
        )
        db.commit()
        cursor.close()
        db.close()

        return redirect(url_for('admin.dashboard'))
    return redirect(url_for('admin.dashboard'))

def admin_settings():
    if 'admin_id' not in session:
        return redirect(url_for('admin.admin_login'))

    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM admin_restaurant WHERE admin_id = %s",
                   (session['admin_id'],))
    admin = cursor.fetchone()

    if not admin:
        cursor.execute("SELECT * FROM staff_accounts WHERE staff_id = %s",
                       (session['admin_id'],))
        staff = cursor.fetchone()
        if staff:
            admin = {
                'admin_id':       staff['staff_id'],
                'admin_username': staff['staff_username'],
                'admin_fullname': staff['full_name'],
                'admin_email':    staff['email'],
                'role':           staff['role'],
                'last_login':     staff['last_login'],
                'created_at':     staff['created_at'],
            }

    cursor.close()
    db.close()
    return render_template('admin/settings.html', admin=admin)

def update_admin_settings():
    if 'admin_id' not in session:
        return redirect(url_for('admin.admin_login'))

    action   = request.form.get('action')
    admin_id = session['admin_id']
    db = get_db()
    cursor = db.cursor(dictionary=True)

    # Check which table this admin lives in
    cursor.execute("SELECT admin_id FROM admin_restaurant WHERE admin_id = %s", (admin_id,))
    is_admin_table = cursor.fetchone() is not None

    if action == 'details':
        fullname = request.form.get('admin_fullname')
        email    = request.form.get('admin_email')
        username = request.form.get('admin_username')

        if is_admin_table:
            cursor.execute("""
                UPDATE admin_restaurant
                SET admin_fullname = %s, admin_email = %s, admin_username = %s
                WHERE admin_id = %s
            """, (fullname, email, username, admin_id))
        else:
            cursor.execute("""
                UPDATE staff_accounts
                SET full_name = %s, email = %s, staff_username = %s
                WHERE staff_id = %s
            """, (fullname, email, username, admin_id))

        db.commit()
        session['admin_username'] = username
        session['toast_message'] = 'Account details updated successfully.'

    elif action == 'password':
        current_password  = request.form.get('current_password')
        new_password      = request.form.get('new_password')
        confirm_password  = request.form.get('confirm_password')

        if is_admin_table:
            cursor.execute("SELECT password_hash FROM admin_restaurant WHERE admin_id = %s",
                           (admin_id,))
        else:
            cursor.execute("SELECT password_hash FROM staff_accounts WHERE staff_id = %s",
                           (admin_id,))
        row = cursor.fetchone()

        if not check_password_hash(row['password_hash'], current_password):
            session['toast_message'] = 'Current password is incorrect.'
        elif new_password != confirm_password:
            session['toast_message'] = 'New passwords do not match.'
        elif len(new_password) < 8:
            session['toast_message'] = 'Password must be at least 8 characters.'
        else:
            hashed = generate_password_hash(new_password)
            if is_admin_table:
                cursor.execute("""
                    UPDATE admin_restaurant SET password_hash = %s WHERE admin_id = %s
                """, (hashed, admin_id))
            else:
                cursor.execute("""
                    UPDATE staff_accounts SET password_hash = %s WHERE staff_id = %s
                """, (hashed, admin_id))
            db.commit()
            session['toast_message'] = 'Password updated successfully.'

    cursor.close()
    db.close()
    return redirect(url_for('admin.admin_settings'))

def manage_theme():
    if request.method == 'POST':
        save_theme({
            'color_primary':     request.form.get('color_primary',     '#8B0000'),
            'color_accent':      request.form.get('color_accent',      '#D4AF37'),
            'color_background':  request.form.get('color_background',  '#F7F4EE'),
            'color_surface':     request.form.get('color_surface',     '#FFFFFF'),
            'color_text':        request.form.get('color_text',        '#2C2416'),
            'color_text_muted':  request.form.get('color_text_muted',  '#9E8C78'),
            'color_sidebar_bg':  request.form.get('color_sidebar_bg',  '#2C2416'),
            'color_sidebar_text':request.form.get('color_sidebar_text','#FFFEF2'),
            'font_body':         request.form.get('font_body',         'Lato'),
            'font_heading':      request.form.get('font_heading',      'Playfair Display'),
            'border_radius':     request.form.get('border_radius',     '2px'),
            'dark_mode':         1 if 'dark_mode' in request.form else 0,
        })
        flash('Theme saved!', 'success')
        return redirect(url_for('admin.manage_theme'))

    theme = get_theme()
    return render_template('admin/theme.html',
                           theme=theme,
                           body_fonts=GOOGLE_FONTS,
                           heading_fonts=HEADING_FONTS)