from app.database import db

def get_all_menu_items():
    return [
        {"name": "Starter 1", "description": "Description of Starter 1", "category": "Starters"},
        {"name": "Main 1", "description": "Description of Main 1", "category": "Mains"},
        {"name": "Dessert 1", "description": "Description of Dessert 1", "category": "Desserts"},
    ]
