import os
from functools import wraps
from flask import session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

# This is the shared SQLAlchemy instance which are imported by all models
db = SQLAlchemy()

def get_db():
    """
    Legacy raw MySQL connection — kept for any queries not yet
    migrated to SQLAlchemy. Will be removed once migration is complete.
    """
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        passwd=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME", "reservations_restaurant_db"),
        connection_timeout=30
    )

def staff_redirect(f):
    """
    Decorator — redirects logged-in staff away from customer-facing pages.
    Kitchen staff → kitchen display. Drivers → driver orders. Admins → dashboard.
    """
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