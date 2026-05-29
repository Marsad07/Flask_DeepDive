from datetime import datetime
from app2.database import db
from app2.models.base_model import BaseModel

class ThemeSettings(BaseModel):
    """Maps to the theme_settings table — single row, id always 1."""
    __tablename__ = "theme_settings"

    id = db.Column(db.Integer, primary_key=True, default=1)
    color_primary = db.Column(db.String(7), default='#8B0000')
    color_accent = db.Column(db.String(7), default='#D4AF37')
    color_background = db.Column(db.String(7), default='#F7F4EE')
    color_surface = db.Column(db.String(7), default='#FFFFFF')
    color_text = db.Column(db.String(7), default='#2C2416')
    color_text_muted = db.Column(db.String(7), default='#9E8C78')
    color_sidebar_bg = db.Column(db.String(7), default='#2C2416')
    color_sidebar_text = db.Column(db.String(7), default='#FFFEF2')
    font_body = db.Column(db.String(100), default='Lato')
    font_heading = db.Column(db.String(100), default='Playfair Display')
    border_radius = db.Column(db.String(10), default='2px')
    dark_mode = db.Column(db.Boolean, default=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow,
                           onupdate=datetime.utcnow)

    # Domain methods
    @classmethod
    def get(cls):
        """Return the single theme settings row."""
        return cls.query.get(1)

    def __repr__(self):
        return f"<ThemeSettings primary={self.color_primary}>"
