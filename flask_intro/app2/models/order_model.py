from datetime import datetime
from app2.database import db
from app2.models.base_model import BaseModel

class Order(BaseModel):
    """Maps to the customer_orders table."""
    __tablename__ = "customer_orders"
    order_id               = db.Column(db.Integer, primary_key=True, autoincrement=True)
    customer_id            = db.Column(db.Integer, db.ForeignKey("customer_accounts.customer_id"), nullable=True)
    guest_fullname         = db.Column(db.String(255), nullable=True)
    guest_email            = db.Column(db.String(255), nullable=True)
    guest_phonenum         = db.Column(db.String(20),  nullable=True)
    order_type             = db.Column(db.String(50),  nullable=False)
    guest_delivery_address = db.Column(db.String(500), nullable=True)
    total_price            = db.Column(db.Numeric(10, 2), nullable=False)
    order_status           = db.Column(db.String(50),  default="pending")
    payment_status         = db.Column(db.String(50),  default="pending")
    payment_method         = db.Column(db.String(50),  nullable=True)
    special_instructions   = db.Column(db.Text,        nullable=True)
    # Using String for date/time and db.Date and db.Time cause issues with SQLite in tests
    order_date             = db.Column(db.String(20),  nullable=True)
    order_time             = db.Column(db.String(20),  nullable=True)
    coupon_code            = db.Column(db.String(50),  nullable=True)
    discount_amount        = db.Column(db.Numeric(10, 2), default=0)
    stripe_payment_intent  = db.Column(db.String(255), nullable=True)
    refund_status          = db.Column(db.String(20),  default="none")
    refunded_at            = db.Column(db.DateTime,    nullable=True)
    refund_amount          = db.Column(db.Numeric(10, 2), nullable=True)
    driver_offer_id        = db.Column(db.Integer,     nullable=True)
    driver_offer_status    = db.Column(db.String(50),  nullable=True)
    assigned_driver_id     = db.Column(db.Integer,     nullable=True)
    estimated_minutes      = db.Column(db.Integer,     nullable=True)
    created_at             = db.Column(db.DateTime,    default=datetime.utcnow)

    # This is to create a relationship to order items
    items = db.relationship("OrderItem", backref="order", lazy=True)

    # Domain methods
    def update_status(self, new_status, estimated_minutes=None):
        """Update order status and optionally set estimated minutes."""
        self.order_status = new_status
        if estimated_minutes:
            self.estimated_minutes = estimated_minutes
        db.session.commit()

    def cancel(self):
        """Cancel this order."""
        self.order_status = "cancelled"
        db.session.commit()

    def mark_refunded(self, amount, partial=False):
        """Record a refund against this order."""
        self.refund_status = "partial" if partial else "refunded"
        self.refund_amount = amount
        self.refunded_at   = datetime.utcnow()
        self.order_status  = "cancelled"
        db.session.commit()

    def offer_driver(self, driver_id):
        """Assign a driver offer to this order."""
        self.driver_offer_id     = driver_id
        self.driver_offer_status = "offered"
        db.session.commit()

    @classmethod
    def accept_driver_offer(cls, order_id):
        """Driver accepted — set assigned_driver_id and status."""
        order = cls.get_by_id(order_id)
        if order:
            order.assigned_driver_id  = order.driver_offer_id
            order.driver_offer_status = "accepted"
            db.session.commit()

    @classmethod
    def decline_driver_offer(cls, order_id):
        """Driver declined — clear offer and revert to pending."""
        order = cls.get_by_id(order_id)
        if order:
            order.driver_offer_id     = None
            order.driver_offer_status = "declined"
            order.order_status        = "pending"
            db.session.commit()

    @classmethod
    def get_today(cls):
        """Return all orders placed today."""
        from datetime import date
        today_str = date.today().strftime('%Y-%m-%d')
        return cls.query.filter(cls.order_date == today_str).all()

    @classmethod
    def get_pending(cls):
        """Return all pending orders."""
        return cls.find(order_status="pending")

    @classmethod
    def get_revenue_today(cls):
        """Return total revenue for today excluding cancelled orders."""
        from datetime import date
        from sqlalchemy import func
        today_str = date.today().strftime('%Y-%m-%d')
        result = db.session.query(func.sum(cls.total_price)).filter(
            cls.order_date == today_str,
            cls.order_status != "cancelled"
        ).scalar()
        return float(result or 0)

    def is_card_paid(self):
        """Returns True if this order was paid by card online."""
        return self.payment_method == "card_online" and self.payment_status == "paid"

    def is_refundable(self):
        return bool(self.is_card_paid() and self.refund_status != "refunded" and self.stripe_payment_intent)

    def __repr__(self):
        return f"<Order #{self.order_id} — {self.order_status}>"

class OrderItem(BaseModel):
    """Maps to the order_items table."""
    __tablename__ = "order_items"

    id           = db.Column(db.Integer, primary_key=True, autoincrement=True)
    order_id     = db.Column(db.Integer, db.ForeignKey("customer_orders.order_id"), nullable=False)
    menu_item_id = db.Column(db.Integer, nullable=True)
    item_name    = db.Column(db.String(255), nullable=False)
    item_price   = db.Column(db.Numeric(10, 2), nullable=False)
    quantity     = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f"<OrderItem {self.item_name} x{self.quantity}>"