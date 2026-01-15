from flask import session
from app.database import db3

def inject_subjects():
    user_id = session.get("user_id")
    if not user_id:
        return dict(sidebar_subjects=[])

    cursor = db3.cursor(dictionary=True)
    cursor.execute(
        "SELECT id, name FROM subjects WHERE user_id=%s",
        (user_id,)
    )
    subjects = cursor.fetchall()

    return dict(sidebar_subjects=subjects)
