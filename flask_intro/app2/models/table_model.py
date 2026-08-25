from datetime import datetime
from app2.database import db
from app2.models.base_model import BaseModel

class RestaurantTable(BaseModel):
    """Maps to the restaurant_customer_tables table."""
    __tablename__ = "restaurant_customer_tables"

    table_id     = db.Column(db.Integer, primary_key=True, autoincrement=True)
    table_number = db.Column(db.Integer, nullable=False, unique=True)
    seats        = db.Column(db.Integer, nullable=False)
    location     = db.Column(db.String(50), nullable=False)
    shape        = db.Column(db.String(20), default='square')
    pos_x        = db.Column(db.Integer, default=0)
    pos_y        = db.Column(db.Integer, default=0)
    is_active    = db.Column(db.Boolean, default=True)

    # Domain methods
    @classmethod
    def get_active(cls):
        """Return all active tables — uses filter instead of find() to handle tinyint(1) comparison."""
        return cls.query.filter(cls.is_active == True).order_by(cls.table_number).all()

    def deactivate(self):
        """Deactivate this table."""
        self.is_active = False
        db.session.commit()

    def __repr__(self):
        return f"<RestaurantTable #{self.table_number} — {self.seats} seats>"