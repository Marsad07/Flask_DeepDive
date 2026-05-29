"""
Integration tests for key HTTP routes.
Uses the Flask test client to make requests and check responses.
"""
import pytest

# Homepage and public routes
class TestPublicRoutes:
    def test_homepage_loads(self, client):
        """Homepage returns 200."""
        response = client.get('/')
        assert response.status_code == 200

    def test_menu_page_loads(self, client):
        response = client.get('/menu', follow_redirects=True)
        assert response.status_code == 200

    def test_reservations_page_loads(self, client):
        response = client.get('/reservations', follow_redirects=True)
        assert response.status_code == 200

    def test_contact_page_loads(self, client):
        """Contact page returns 200."""
        response = client.get('/contact')
        assert response.status_code == 200

    def test_about_page_loads(self, client):
        """About page returns 200."""
        response = client.get('/about')
        assert response.status_code == 200


# Auth routes
class TestAuthRoutes:
    def test_login_page_loads(self, client):
        """Customer login page returns 200."""
        response = client.get('/auth/login')
        assert response.status_code == 200

    def test_register_page_loads(self, client):
        """Register page returns 200."""
        response = client.get('/auth/register')
        assert response.status_code == 200

    def test_login_wrong_credentials(self, client):
        """Login with wrong credentials stays on login page."""
        response = client.post('/auth/login', data={
            'customer_email': 'wrong@example.com',
            'customer_password': 'wrongpassword'
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'Incorrect' in response.data or b'incorrect' in response.data

    @pytest.mark.skip(reason="Register uses raw SQL insert — not yet migrated to ORM, incompatible with SQLite test DB")
    def test_register_and_login(self, client, app):
        import uuid
        unique_email = f'test_{uuid.uuid4().hex[:8]}@example.com'
        response = client.post('/auth/register', data={
            'customer_fullname': 'Test Customer',
            'customer_email': unique_email,
            'customer_phonenum': '07123456789',
            'customer_password': 'testpassword123'
        }, follow_redirects=True)
        assert response.status_code == 200

    def test_dashboard_redirects_when_not_logged_in(self, client):
        """Customer dashboard redirects to login if not authenticated."""
        response = client.get('/auth/dashboard')
        assert response.status_code in (301, 302)

# Admin routes
class TestAdminRoutes:
    def test_admin_login_page_loads(self, client):
        """Admin login page returns 200."""
        response = client.get('/admin/login')
        assert response.status_code == 200

    def test_admin_dashboard_redirects_when_not_logged_in(self, client):
        """Admin dashboard redirects to login if not authenticated."""
        response = client.get('/admin/dashboard')
        assert response.status_code in (301, 302)

    def test_admin_orders_redirects_when_not_logged_in(self, client):
        """Admin orders page redirects to login if not authenticated."""
        response = client.get('/admin/view_all_orders')
        assert response.status_code in (301, 302)

    def test_admin_menu_redirects_when_not_logged_in(self, client):
        """Admin menu page redirects to login if not authenticated."""
        response = client.get('/admin/menu')
        assert response.status_code in (301, 302)

    def test_admin_analytics_redirects_when_not_logged_in(self, client):
        """Admin analytics page redirects to login if not authenticated."""
        response = client.get('/admin/analytics')
        assert response.status_code in (301, 302)

# Cart routes
class TestCartRoutes:
    def test_cart_page_loads(self, client):
        response = client.get('/cart', follow_redirects=True)
        assert response.status_code == 200

    @pytest.mark.skip(reason="Cart add uses raw SQL — not yet migrated to ORM, incompatible with SQLite test DB")
    def test_add_to_cart(self, client, app):
        response = client.post('/cart/add/999', follow_redirects=True)
        assert response.status_code in (200, 404, 302, 308)

# Coupon logic tests
class TestCouponLogic:
    def test_apply_invalid_coupon(self, client):
        """Applying a non-existent coupon returns error JSON."""
        response = client.post('/checkout/apply-coupon',
                               json={'code': 'INVALIDCODE', 'total': 50.00})
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is False
        assert 'Invalid' in data['message'] or 'invalid' in data['message']

    def test_apply_empty_coupon_code(self, client):
        """Applying an empty coupon code returns error JSON."""
        response = client.post('/checkout/apply-coupon',
                               json={'code': '', 'total': 50.00})
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is False