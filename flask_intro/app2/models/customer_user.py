from flask_login import UserMixin

class CustomerUser(UserMixin):
    def __init__(self, data):
        self.id = data["customer_id"]
        self.email = data["customer_email"]
        self.name = data.get("customer_fullname", "")