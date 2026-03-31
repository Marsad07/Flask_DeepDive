import mysql.connector

db_config = {
    "host": "localhost",
    "user": "root",
    "passwd": "PYTHONCOURSE",
    "database": "reservations_restaurant_db"
}

def get_db():
    return mysql.connector.connect(**db_config)