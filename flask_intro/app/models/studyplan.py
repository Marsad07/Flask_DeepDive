from flask_intro.app.database import db3

def get_plans_for_user(user_id):
    cursor = db3.cursor(dictionary=True)
    cursor.execute(
        "SELECT id, title FROM study_plans WHERE user_id=%s ORDER BY id DESC",
        (user_id,)
    )
    return cursor.fetchall()

def get_tasks_for_user(user_id):
    cursor = db3.cursor(dictionary=True)
    cursor.execute(
        "SELECT id, task_name, priority FROM tasks_new WHERE user_id=%s ORDER BY priority DESC, task_name ASC",
        (user_id,)
    )
    return cursor.fetchall()

def create_plan(user_id, title):
    cursor = db3.cursor(dictionary=True)
    cursor.execute(
        "INSERT INTO study_plans (user_id, title) VALUES (%s, %s)",
        (user_id, title)
    )
    db3.commit()
    return cursor.lastrowid

def get_plan(user_id, plan_id):
    cursor = db3.cursor(dictionary=True)
    cursor.execute(
        "SELECT id, title FROM study_plans WHERE id=%s AND user_id=%s",
        (plan_id, user_id)
    )
    return cursor.fetchone()

def generate_items_for_plan(user_id, plan_id, task_ids):
    cursor = db3.cursor(dictionary=True)

    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    day_index = 0

    for task_id in task_ids:
        cursor.execute(
            """
            INSERT INTO study_plan_items
            (plan_id, task_id, day_of_week, start_time, end_time)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                plan_id,
                task_id,
                days[day_index],
                "10:00",
                "11:00"
            )
        )
        day_index = (day_index + 1) % len(days)
    db3.commit()

def get_plan_items(user_id, plan_id):
    cursor = db3.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT
            i.day_of_week,
            i.start_time,
            i.end_time,
            t.task_name,
            t.priority,
            t.status
        FROM study_plan_items i
        JOIN study_plans p ON p.id = i.plan_id
        JOIN tasks_new t ON t.id = i.task_id
        WHERE p.user_id = %s AND p.id = %s
        ORDER BY
            FIELD(i.day_of_week,'Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'),
            i.start_time
        """,
        (user_id, plan_id)
    )
    return cursor.fetchall()

def delete_plan(user_id, plan_id):
    cursor = db3.cursor(dictionary=True)

    cursor.execute(
        "DELETE i FROM study_plan_items i "
        "JOIN study_plans p ON p.id = i.plan_id "
        "WHERE p.user_id = %s AND p.id = %s",
        (user_id, plan_id)
    )

    cursor.execute(
        "DELETE FROM study_plans WHERE user_id=%s AND id=%s",
        (user_id, plan_id)
    )
    db3.commit()
    return cursor.rowcount > 0

