import mysql.connector
from functools import wraps
from flask import session, redirect, url_for

db_config = {
    "host": "localhost",
    "user": "root",
    "passwd": "PYTHONCOURSE",
    "database": "reservations_restaurant_db"
}

def get_db():
    return mysql.connector.connect(
        **db_config,
        connection_timeout=30
    )

def staff_redirect(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        role = session.get('staff_role')
        if role == 'kitchen':
            return redirect(url_for('staff.kitchen_display'))
        elif role == 'driver':
            return redirect(url_for('staff.driver_orders'))
        elif role == 'admin':
            return redirect(url_for('admin.dashboard'))
        return f(*args, **kwargs)
    return decorated_function