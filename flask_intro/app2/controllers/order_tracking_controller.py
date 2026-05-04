from flask import render_template, request, session
import requests
from app2.database import get_db
from flask_socketio import join_room
from app2 import socketio

def track_order(order_number):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    verified = False
    order = None
    items = []
    error = None
    restaurant = None
    route_coords = None
    customer_lat = None
    customer_lng = None

    # Check if logged in customer or guest
    customer_id = session.get('customer_id')
    if customer_id:
        customer_email = session.get('customer_email')
    else:
        customer_email = request.form.get('guest_email')

    if request.method == 'POST' or customer_id:
        cursor.execute("""
            SELECT * FROM customer_orders 
            WHERE CONCAT('ORD-', DATE_FORMAT(created_at, '%Y%m%d'), '-', 
            LPAD((SELECT COUNT(*) FROM customer_orders co2 
            WHERE DATE(co2.created_at) = DATE(customer_orders.created_at) 
            AND co2.order_id <= customer_orders.order_id), 3, '0')) = %s
        """, (order_number,))
        order = cursor.fetchone()

        if order:
            if customer_id:
                verified = True
            elif customer_email and customer_email.lower() == order['guest_email'].lower():
                verified = True
            else:
                error = "We couldn't find an order with that email. Please try again."
                order = None
        else:
            error = "Order not found"

    if order and verified:
        # Fetch order items
        db2 = get_db()
        cursor2 = db2.cursor(dictionary=True)
        cursor2.execute("SELECT * FROM order_items WHERE order_id = %s", (order['order_id'],))
        items = cursor2.fetchall()
        cursor2.close()
        db2.close()

        # Fetch restaurant location
        db3 = get_db()
        cursor3 = db3.cursor(dictionary=True)
        cursor3.execute("""
            SELECT latitude, longitude, address 
            FROM restaurant_info 
            WHERE latitude IS NOT NULL 
            LIMIT 1
        """)
        restaurant = cursor3.fetchone()
        cursor3.close()
        db3.close()

        # Calculate delivery route if applicable
        if order['order_type'] == 'delivery' and restaurant and order.get('guest_delivery_address'):
            api_key = ('eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6'
                       'IjlhM2ZkYzcyOTQ4YzQ3YzE4NjlkYWI3MmNhMmYwMjFkIiwiaCI6Im11cm11cjY0In0=')
            route_coords, customer_lat, customer_lng = get_route_coordinates(
                float(restaurant['latitude']),
                float(restaurant['longitude']),
                order['guest_delivery_address'],
                api_key
            )

    # Fetch branding for the template
    db_b = get_db()
    cursor_b = db_b.cursor(dictionary=True)
    cursor_b.execute("SELECT * FROM restaurant_branding LIMIT 1")
    branding = cursor_b.fetchone()
    cursor_b.close()
    db_b.close()

    cursor.close()
    db.close()

    # Use customer template if logged in, base template for guests
    template = 'orders/tracking.html' if customer_id else 'orders/tracking.html'

    return render_template(
        template,
        order=order,
        items=items,
        error=error,
        order_number=order_number,
        verified=verified,
        restaurant=restaurant,
        route_coords=route_coords,
        customer_lat=customer_lat,
        customer_lng=customer_lng,
        branding=branding
    )

def get_route_coordinates(restaurant_lat, restaurant_lng, delivery_address, api_key):
    try:
        # Geocode the delivery address
        geocode_response = requests.get(
            'https://nominatim.openstreetmap.org/search',
            params={
                'q': delivery_address,
                'format': 'json',
                'limit': 1,
                'countrycodes': 'gb'
            },
            headers={'User-Agent': 'RestaurantApp/1.0'}
        )
        geocode_data = geocode_response.json()
        print(f"Nominatim result: {geocode_data}")

        if not geocode_data:
            print("Nominatim found nothing")
            return None, None, None

        customer_lat = float(geocode_data[0]['lat'])
        customer_lng = float(geocode_data[0]['lon'])

        # Get driving route
        directions_response = requests.post(
            'https://api.openrouteservice.org/v2/directions/driving-car/geojson',
            json={'coordinates': [[restaurant_lng, restaurant_lat], [customer_lng, customer_lat]]},
            headers={
                'Authorization': api_key,
                'Content-Type': 'application/json'
            }
        )
        directions_data = directions_response.json()

        if 'features' not in directions_data:
            print(f"Directions failed: {directions_data}")
            return None, None, None

        route_coords = directions_data['features'][0]['geometry']['coordinates']
        route_coords = [[c[1], c[0]] for c in route_coords]
        return route_coords, customer_lat, customer_lng

    except Exception as e:
        print(f"Route error: {e}")
        return None, None, None


@socketio.on('join_order')
def handle_join(data):
    order_id = data.get('order_id')
    join_room(f'order_{order_id}')