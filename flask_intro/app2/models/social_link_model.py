from datetime import datetime
from app2.database import db
from app2.models.base_model import BaseModel

class SocialLink(BaseModel):
    """Maps to the social_links table."""
    __tablename__ = "social_links"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    platform = db.Column(db.String(50), nullable=False)
    url = db.Column(db.String(255), nullable=False)
    icon_class = db.Column(db.String(100), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    display_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Domain methods

    @classmethod
    def get_active(cls):
        """Return all active social links ordered by display_order."""
        return cls.query.filter_by(is_active=True).order_by(cls.display_order).all()

    def toggle_active(self):
        """Toggle this link between active and inactive."""
        self.is_active = not self.is_active
        db.session.commit()

    def __repr__(self):
        return f"<SocialLink {self.platform} — {self.url}>"
