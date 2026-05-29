"""
Unit tests for ORM models.
Tests the BaseModel methods and domain logic without hitting a real DB.
"""
import pytest
from app2.database import db
from app2.models.customer_user import CustomerUser
from app2.models.order_model import Order, OrderItem
from app2.models.menu_model import MenuItem


# CustomerUser model tests
class TestCustomerUser:
    def test_create_customer(self, app):
        """CustomerUser.create() inserts a row and returns the instance."""
        with app.app_context():
            user = CustomerUser.create(
                customer_fullname='Test User',
                customer_email='test@example.com',
                customer_password_hash='hashed_password'
            )
            assert user.customer_id is not None
            assert user.customer_fullname == 'Test User'
            assert user.customer_email == 'test@example.com'

    def test_get_by_email(self, app):
        """CustomerUser.get_by_email() returns correct user."""
        with app.app_context():
            CustomerUser.create(
                customer_fullname='Email Test',
                customer_email='emailtest@example.com',
                customer_password_hash='hash'
            )
            user = CustomerUser.get_by_email('emailtest@example.com')
            assert user is not None
            assert user.customer_fullname == 'Email Test'

    def test_get_by_email_not_found(self, app):
        """CustomerUser.get_by_email() returns None for unknown email."""
        with app.app_context():
            user = CustomerUser.get_by_email('doesnotexist@example.com')
            assert user is None

    def test_get_by_id(self, app):
        """CustomerUser.get_by_id() returns correct user."""
        with app.app_context():
            created = CustomerUser.create(
                customer_fullname='ID Test',
                customer_email='idtest@example.com',
                customer_password_hash='hash'
            )
            found = CustomerUser.get_by_id(created.customer_id)
            assert found is not None
            assert found.customer_email == 'idtest@example.com'

    def test_set_and_check_password(self, app):
        """set_password hashes correctly, check_password validates correctly."""
        with app.app_context():
            user = CustomerUser.create(
                customer_fullname='Password Test',
                customer_email='pwtest@example.com',
                customer_password_hash='placeholder'
            )
            user.set_password('mysecurepassword')
            assert user.check_password('mysecurepassword') is True
            assert user.check_password('wrongpassword') is False

    def test_get_id_returns_string(self, app):
        """get_id() must return a string for Flask-Login."""
        with app.app_context():
            user = CustomerUser.create(
                customer_fullname='Login Test',
                customer_email='logintest@example.com',
                customer_password_hash='hash'
            )
            assert isinstance(user.get_id(), str)

    def test_delete_customer(self, app):
        """delete() removes the row from the DB."""
        with app.app_context():
            user = CustomerUser.create(
                customer_fullname='Delete Test',
                customer_email='deletetest@example.com',
                customer_password_hash='hash'
            )
            user_id = user.customer_id
            user.delete()
            assert CustomerUser.get_by_id(user_id) is None


# Order model tests
class TestOrder:
    def test_create_order(self, app):
        """Order.create() inserts a row correctly."""
        with app.app_context():
            order = Order.create(
                order_type='collection',
                total_price=25.00,
                order_status='pending',
                payment_method='cash',
                payment_status='pending'
            )
            assert order.order_id is not None
            assert order.order_status == 'pending'
            assert float(order.total_price) == 25.00

    def test_update_status(self, app):
        """update_status() changes order_status correctly."""
        with app.app_context():
            order = Order.create(
                order_type='collection',
                total_price=10.00,
                order_status='pending',
                payment_method='cash',
                payment_status='pending'
            )
            order.update_status('confirmed')
            assert order.order_status == 'confirmed'

    def test_update_status_with_minutes(self, app):
        """update_status() also sets estimated_minutes when provided."""
        with app.app_context():
            order = Order.create(
                order_type='collection',
                total_price=10.00,
                order_status='pending',
                payment_method='cash',
                payment_status='pending'
            )
            order.update_status('preparing', estimated_minutes=20)
            assert order.order_status == 'preparing'
            assert order.estimated_minutes == 20

    def test_cancel_order(self, app):
        """cancel() sets order_status to cancelled."""
        with app.app_context():
            order = Order.create(
                order_type='collection',
                total_price=15.00,
                order_status='confirmed',
                payment_method='cash',
                payment_status='pending'
            )
            order.cancel()
            assert order.order_status == 'cancelled'

    def test_mark_refunded_full(self, app):
        """mark_refunded() sets refund_status to refunded for full refunds."""
        with app.app_context():
            order = Order.create(
                order_type='collection',
                total_price=30.00,
                order_status='completed',
                payment_method='card_online',
                payment_status='paid',
                stripe_payment_intent='pi_test_123'
            )
            order.mark_refunded(30.00)
            assert order.refund_status == 'refunded'
            assert float(order.refund_amount) == 30.00
            assert order.order_status == 'cancelled'
            assert order.refunded_at is not None

    def test_mark_refunded_partial(self, app):
        """mark_refunded() sets refund_status to partial for partial refunds."""
        with app.app_context():
            order = Order.create(
                order_type='collection',
                total_price=30.00,
                order_status='completed',
                payment_method='card_online',
                payment_status='paid',
                stripe_payment_intent='pi_test_456'
            )
            order.mark_refunded(10.00, partial=True)
            assert order.refund_status == 'partial'
            assert float(order.refund_amount) == 10.00

    def test_is_card_paid(self, app):
        """is_card_paid() returns True only for card_online + paid orders."""
        with app.app_context():
            card_order = Order.create(
                order_type='collection',
                total_price=20.00,
                order_status='completed',
                payment_method='card_online',
                payment_status='paid'
            )
            cash_order = Order.create(
                order_type='collection',
                total_price=20.00,
                order_status='completed',
                payment_method='cash',
                payment_status='pending'
            )
            assert card_order.is_card_paid() is True
            assert cash_order.is_card_paid() is False

    def test_is_refundable(self, app):
        """is_refundable() returns True only when card paid, not refunded, has intent."""
        with app.app_context():
            refundable = Order.create(
                order_type='collection',
                total_price=20.00,
                order_status='completed',
                payment_method='card_online',
                payment_status='paid',
                stripe_payment_intent='pi_test_789'
            )
            not_refundable = Order.create(
                order_type='collection',
                total_price=20.00,
                order_status='completed',
                payment_method='cash',
                payment_status='pending'
            )
            assert refundable.is_refundable() is True
            assert not_refundable.is_refundable() is False

    def test_get_pending(self, app):
        """get_pending() returns only pending orders."""
        with app.app_context():
            Order.create(
                order_type='collection', total_price=5.00,
                order_status='pending', payment_method='cash', payment_status='pending'
            )
            Order.create(
                order_type='collection', total_price=5.00,
                order_status='completed', payment_method='cash', payment_status='pending'
            )
            pending = Order.get_pending()
            assert all(o.order_status == 'pending' for o in pending)


# MenuItem model tests
class TestMenuItem:
    def test_create_menu_item(self, app):
        """MenuItem.create() inserts correctly."""
        with app.app_context():
            item = MenuItem.create(
                item_name='Prawn Toast',
                price=6.50,
                category='Starters',
                is_available=True
            )
            assert item.id is not None
            assert item.item_name == 'Prawn Toast'
            assert float(item.price) == 6.50

    def test_mark_sold_out(self, app):
        """mark_sold_out() sets is_available to False."""
        with app.app_context():
            item = MenuItem.create(
                item_name='Spring Rolls',
                price=5.00,
                category='Starters',
                is_available=True
            )
            item.mark_sold_out()
            assert item.is_available is False

    def test_mark_available(self, app):
        """mark_available() sets is_available back to True."""
        with app.app_context():
            item = MenuItem.create(
                item_name='Dumplings',
                price=7.00,
                category='Starters',
                is_available=False
            )
            item.mark_available()
            assert item.is_available is True

    def test_get_available(self, app):
        """get_available() returns only available items."""
        with app.app_context():
            MenuItem.create(item_name='Available Item', price=5.00,
                            category='Mains', is_available=True)
            MenuItem.create(item_name='Sold Out Item', price=5.00,
                            category='Mains', is_available=False)
            available = MenuItem.get_available()
            assert all(i.is_available for i in available)

    def test_to_dict(self, app):
        """to_dict() returns a plain dict with all columns."""
        with app.app_context():
            item = MenuItem.create(
                item_name='Dict Test Item',
                price=8.00,
                category='Desserts',
                is_available=True
            )
            d = item.to_dict()
            assert isinstance(d, dict)
            assert d['item_name'] == 'Dict Test Item'
            assert 'price' in d