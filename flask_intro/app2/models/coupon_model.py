from datetime import datetime
from app2.database import db
from app2.models.base_model import BaseModel

class Coupon(BaseModel):
    """Maps to the coupons table."""
    __tablename__ = "coupons"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    code = db.Column(db.String(50), nullable=False, unique=True)
    discount_type = db.Column(db.String(10), nullable=False)  # percent / fixed
    discount_value = db.Column(db.Numeric(10, 2), nullable=False)
    assigned_email = db.Column(db.String(255), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    uses_limit = db.Column(db.Integer, default=1)
    uses_count = db.Column(db.Integer, default=0)
    expires_at = db.Column(db.String(20), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Domain methods 
    def is_valid(self):
        """Returns True if the coupon can still be used."""
        from datetime import date
        if not self.is_active:
            return False
        if self.uses_count >= self.uses_limit:
            return False
        if self.expires_at and self.expires_at < str(date.today()):
            return False
        return True

    def apply(self, order_total):
        """Calculate and return the discount amount for a given order total."""
        if self.discount_type == 'percent':
            return round(float(order_total) * float(self.discount_value) / 100, 2)
        return min(float(self.discount_value), float(order_total))

    def increment_uses(self):
        """Increment the usage count after a successful order."""
        self.uses_count += 1
        db.session.commit()

    def toggle_active(self):
        """Toggle the coupon between active and inactive."""
        self.is_active = not self.is_active
        db.session.commit()

    @classmethod
    def get_by_code(cls, code):
        """Find a coupon by its code."""
        return cls.first(code=code.strip().upper())

    def __repr__(self):
        return f"<Coupon {self.code} — {self.discount_type} {self.discount_value}>"