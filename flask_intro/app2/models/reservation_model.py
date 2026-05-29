from datetime import datetime
from app2.database import db
from app2.models.base_model import BaseModel

class Reservation(BaseModel):
    """Maps to the reservations_restaurant table."""
    __tablename__ = "reservations_restaurant"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    customer_fullname = db.Column(db.String(255), nullable=False)
    customer_email = db.Column(db.String(255), nullable=False)
    customer_phone = db.Column(db.String(20), nullable=True)
    reservation_date = db.Column(db.String(20), nullable=False)
    reservation_time = db.Column(db.String(20), nullable=False)
    num_of_guests = db.Column(db.Integer, nullable=False)
    table_number = db.Column(db.Integer, nullable=True)
    special_requests = db.Column(db.Text, nullable=True)
    reservation_status = db.Column(db.String(50), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Domain methods
    def confirm(self):
        """Confirm this reservation."""
        self.reservation_status = 'confirmed'
        db.session.commit()

    def cancel(self):
        """Cancel this reservation."""
        self.reservation_status = 'cancelled'
        db.session.commit()

    def complete(self):
        """Mark this reservation as completed."""
        self.reservation_status = 'completed'
        db.session.commit()

    @classmethod
    def get_upcoming(cls):
        """Return all pending and confirmed reservations."""
        return cls.query.filter(
            cls.reservation_status.in_(['pending', 'confirmed'])
        ).all()

    @classmethod
    def get_by_email(cls, email):
        """Return all reservations for a given email address."""
        return cls.find(customer_email=email)

    def __repr__(self):
        return f"<Reservation #{self.id} — {self.customer_fullname} on {self.reservation_date}>"