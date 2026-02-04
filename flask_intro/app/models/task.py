from app.database import db

class Task(db.Model):
    __tablename__ = 'tasks_new'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(255), nullable=False)

    status = db.Column(db.String(50), nullable=True)