from app2.database import get_db

def add_category(category_name):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("INSERT INTO menu_categories (category_name) VALUES (%s)",
                   (category_name, ))
    db.commit()
    db.close()
    cursor.close()

def get_category():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM menu_categories ORDER BY category_name ASC")
    categories = cursor.fetchall()
    cursor.close()
    return categories

def delete_category(category_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM menu_categories WHERE category_id = %s", (category_id,))
    db.commit()
    cursor.close()
    db.close()