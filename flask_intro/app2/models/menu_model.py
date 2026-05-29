from app2.database import db
from app2.models.base_model import BaseModel

class MenuItem(BaseModel):
    """Maps to the menu_items table."""
    __tablename__ = "menu_items"

    id           = db.Column(db.Integer, primary_key=True, autoincrement=True)
    item_name    = db.Column(db.String(255), nullable=False)
    description  = db.Column(db.Text, nullable=True)
    price        = db.Column(db.Numeric(10, 2), nullable=False)
    category     = db.Column(db.String(255), nullable=True)
    image_url    = db.Column(db.String(255), nullable=True)
    is_available = db.Column(db.Boolean, default=True)

    # Domain methods
    @classmethod
    def get_by_category(cls, category_name):
        """Return all available items in a given category."""
        return cls.query.filter_by(
            category=category_name,
            is_available=True
        ).all()

    @classmethod
    def get_available(cls):
        """Return all available menu items."""
        return cls.find(is_available=True)

    def mark_sold_out(self):
        """Mark this item as unavailable (sold out)."""
        self.is_available = False
        db.session.commit()

    def mark_available(self):
        """Mark this item as available again."""
        self.is_available = True
        db.session.commit()

    def __repr__(self):
        return f"<MenuItem {self.item_name} — £{self.price}>"

class MenuCategory(BaseModel):
    """Maps to the menu_categories table."""
    __tablename__ = "menu_categories"

    id            = db.Column(db.Integer, primary_key=True, autoincrement=True)
    category_name = db.Column(db.String(255), nullable=False, unique=True)

    def __repr__(self):
        return f"<MenuCategory {self.category_name}>"