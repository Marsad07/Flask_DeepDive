from datetime import datetime
from app2.database import db
from app2.models.base_model import BaseModel

class StaffAccount(BaseModel):
    """Maps to the staff_accounts table."""
    __tablename__ = "staff_accounts"

    staff_id       = db.Column(db.Integer,     primary_key=True, autoincrement=True)
    staff_username = db.Column(db.String(100),  nullable=False, unique=True)
    email          = db.Column(db.String(255),  nullable=True)
    password_hash  = db.Column(db.String(255),  nullable=False)
    full_name      = db.Column(db.String(150),  nullable=True)
    role           = db.Column(db.String(50),   nullable=False)  # admin / driver / kitchen
    is_active      = db.Column(db.Integer,      default=1)
    is_available   = db.Column(db.Boolean,      default=True)
    created_at     = db.Column(db.DateTime,     nullable=True)
    last_login     = db.Column(db.DateTime,     nullable=True)

    # Domain methods
    def set_password(self, plain_text_password):
        """Hash and store a new password."""
        from werkzeug.security import generate_password_hash
        self.password_hash = generate_password_hash(plain_text_password)
        db.session.commit()

    def check_password(self, plain_text_password):
        """Return True if the plain text password matches the stored hash."""
        from werkzeug.security import check_password_hash
        return check_password_hash(self.password_hash, plain_text_password)

    def disable(self):
        """Disable this staff account."""
        self.is_active = 0
        db.session.commit()

    def enable(self):
        """Re-enable this staff account."""
        self.is_active = 1
        db.session.commit()

    @classmethod
    def get_drivers(cls):
        """Return all active driver accounts."""
        return cls.query.filter_by(role='driver', is_active=1).all()

    @classmethod
    def get_by_username(cls, username):
        """Find a staff account by username."""
        return cls.first(staff_username=username)

    def __repr__(self):
        return f"<StaffAccount {self.staff_username} — {self.role}>"