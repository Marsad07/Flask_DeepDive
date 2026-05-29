from datetime import datetime
from app2.database import db
from app2.models.base_model import BaseModel

class StaffAccount(BaseModel):
    """Maps to the staff_accounts table."""
    __tablename__ = "staff_accounts"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    staff_name = db.Column(db.String(255), nullable=False)
    staff_username = db.Column(db.String(255), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=True)
    role = db.Column(db.String(50), nullable=True)  # admin / driver / kitchen
    is_active = db.Column(db.Boolean, default=True)
    full_name = db.Column(db.String(255), nullable=True)

    # Domain methods

    def set_password(self, plain_text_password):
        """Hash and store a new password."""
        from werkzeug.security import generate_password_hash
        self.password = generate_password_hash(plain_text_password)
        db.session.commit()

    def check_password(self, plain_text_password):
        """Return True if the plain text password matches the stored hash."""
        from werkzeug.security import check_password_hash
        return check_password_hash(self.password, plain_text_password)

    def disable(self):
        """Disable this staff account."""
        self.is_active = False
        db.session.commit()

    def enable(self):
        """Re-enable this staff account."""
        self.is_active = True
        db.session.commit()

    @classmethod
    def get_drivers(cls):
        """Return all active driver accounts."""
        return cls.query.filter_by(role='driver', is_active=True).all()

    @classmethod
    def get_by_username(cls, username):
        """Find a staff account by username."""
        return cls.first(staff_username=username)

    def __repr__(self):
        return f"<StaffAccount {self.staff_username} — {self.role}>"
