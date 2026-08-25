from datetime import datetime
from app2.database import db
from app2.models.base_model import BaseModel

class Reservation(BaseModel):
    """Maps to the reservations_restaurant table."""
    __tablename__ = "reservations_restaurant"

    customer_id         = db.Column(db.Integer, primary_key=True, autoincrement=True)
    customer_fullname   = db.Column(db.String(255), nullable=False)
    customer_email      = db.Column(db.String(255), nullable=True)
    customer_phonenum   = db.Column(db.String(30),  nullable=True)
    reservation_date    = db.Column(db.String(20),  nullable=True)
    reservation_time    = db.Column(db.String(20),  nullable=True)
    num_of_guests       = db.Column(db.Integer,     nullable=True)
    table_number        = db.Column(db.Integer,     nullable=True)
    special_requests    = db.Column(db.String(255), nullable=True)
    reservation_status  = db.Column(db.String(50),  nullable=True)
    reservation_createdate = db.Column(db.DateTime, nullable=True)

    def confirm(self):
        self.reservation_status = 'Confirmed'
        db.session.commit()

    def cancel(self):
        self.reservation_status = 'Cancelled'
        db.session.commit()

    def complete(self):
        self.reservation_status = 'Completed'
        db.session.commit()

    @classmethod
    def get_upcoming(cls):
        return cls.query.filter(
            cls.reservation_status.in_(['Confirmed', 'pending'])
        ).all()

    @classmethod
    def get_by_email(cls, email):
        return cls.find(customer_email=email)

    def __repr__(self):
        return f"<Reservation #{self.customer_id} — {self.customer_fullname}>"