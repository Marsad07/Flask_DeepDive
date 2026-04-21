from werkzeug.security import generate_password_hash
import mysql.connector

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="your_mysql_password",
    database="reservations_restaurant_db"
)

cursor = db.cursor()

# This hashes the password
new_password = "temppassword"  # The current admin password
hashed = generate_password_hash(new_password)

# This updates the database with the password
cursor.execute("UPDATE admin_restaurant SET password_hash = %s WHERE admin_username = 'admin'",
               (hashed,))
db.commit()

print("Password hashed successfully!")