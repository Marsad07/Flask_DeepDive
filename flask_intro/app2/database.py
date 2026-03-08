import mysql.connector

restaurant_db1 = mysql.connector.connect(
    host="localhost",
    user="root",
    passwd="PYTHONCOURSE",
    database="reservations_restaurant_db"
)