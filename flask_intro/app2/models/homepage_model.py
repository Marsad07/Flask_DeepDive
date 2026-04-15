from app2.database import get_db

def get_branding():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM restaurant_branding LIMIT 1")
    result = cursor.fetchone()
    cursor.close()
    db.close()
    return result

def update_branding(use_logo, logo_path, restaurant_name, restaurant_motto):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        UPDATE restaurant_branding 
        SET use_logo=%s, logo_path=%s, restaurant_name=%s, restaurant_motto=%s
    """, (use_logo, logo_path, restaurant_name, restaurant_motto))
    db.commit()
    cursor.close()
    db.close()

def get_reviews():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM reviews WHERE is_visible = TRUE ORDER BY review_id")
    result = cursor.fetchall()
    cursor.close()
    db.close()
    return result

def get_all_reviews():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM reviews ORDER BY review_id")
    result = cursor.fetchall()
    cursor.close()
    db.close()
    return result

def update_review(review_id, reviewer_name, review_text, rating, is_visible):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        UPDATE reviews SET reviewer_name=%s, review_text=%s, rating=%s, is_visible=%s
        WHERE review_id=%s
    """, (reviewer_name, review_text, rating, is_visible, review_id))
    db.commit()
    cursor.close()
    db.close()

def add_review(reviewer_name, review_text, rating):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        INSERT INTO reviews (reviewer_name, review_text, rating)
        VALUES (%s, %s, %s)
    """, (reviewer_name, review_text, rating))
    db.commit()
    cursor.close()
    db.close()

def delete_review(review_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM reviews WHERE review_id=%s", (review_id,))
    db.commit()
    cursor.close()
    db.close()

def get_dishes():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM signature_dishes ORDER BY dish_id")
    result = cursor.fetchall()
    cursor.close()
    db.close()
    return result

def update_dish(dish_key, dish_name, dish_description):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        UPDATE signature_dishes SET dish_name=%s, dish_description=%s
        WHERE dish_key=%s
    """, (dish_name, dish_description, dish_key))
    db.commit()
    cursor.close()
    db.close()