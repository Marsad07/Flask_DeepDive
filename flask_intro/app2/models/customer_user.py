from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from app2.database import db
from app2.models.base_model import BaseModel

class CustomerUser(UserMixin, BaseModel):
    """
    Maps to customer_accounts table.
    Inherits UserMixin for Flask-Login compatibility.
    Single definition — replaces the duplicate in __init__.py.
    """
    __tablename__ = "customer_accounts"

    customer_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    customer_fullname = db.Column(db.String(255), nullable=False)
    customer_email = db.Column(db.String(255), nullable=False, unique=True)
    customer_password_hash = db.Column(db.String(255), nullable=False)

    # Flask-Login required
    def get_id(self):
        """Flask-Login uses this to identify the user in the session."""
        return str(self.customer_id)

    # Domain methods
    def set_password(self, plain_text_password):
        self.customer_password_hash = generate_password_hash(plain_text_password)
        db.session.commit()

    def check_password(self, plain_text_password):
        return check_password_hash(self.customer_password_hash, plain_text_password)

    @classmethod
    def get_by_email(cls, email):
        """Find a customer by email address."""
        return cls.first(customer_email=email)

    @classmethod
    def get_by_id(cls, customer_id):
        """Find a customer by ID — used by Flask-Login's user_loader."""
        return cls.query.get(int(customer_id))

    @classmethod
    def register(cls, fullname, email, password):
        """
        Create a new customer account with a hashed password.
        Returns the new CustomerUser instance.
        """
        hashed = generate_password_hash(password)
        return cls.create(
            customer_fullname=fullname,
            customer_email=email,
            password=hashed
        )

    def __repr__(self):
        return f"<CustomerUser #{self.customer_id} — {self.customer_email}>"