import pytest
import os
from app2 import create_app
from app2.database import db

# This must happen before create_app() is called
# Forces SQLite in-memory so tests never touch the real MySQL DB
os.environ['FLASK_ENV'] = 'testing'
os.environ['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'

@pytest.fixture(scope='session')
def app():
    """Create the Flask app in testing mode for the whole test session."""
    app = create_app()

    # Override DB URI after app creation to guarantee SQLite
    app.config.update({
        'TESTING': True,
        'WTF_CSRF_ENABLED': False,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SECRET_KEY': 'test-secret-key',
        'SQLALCHEMY_ECHO': False,
    })

    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture(scope='function')
def client(app):
    """A test client for making HTTP requests."""
    return app.test_client()

@pytest.fixture(scope='function')
def runner(app):
    """A test CLI runner."""
    return app.test_cli_runner()