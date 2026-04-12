from app2.database import get_db

def get_image(image_key):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT image_path FROM images WHERE image_key=%s", (image_key,))
    row = cursor.fetchone()
    return row[0] if row else None

def set_image(image_key, image_path):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        INSERT INTO images (image_key, image_path)
        VALUES (%s, %s)
        ON DUPLICATE KEY UPDATE image_path = VALUES(image_path)
    """, (image_key, image_path))
    db.commit()