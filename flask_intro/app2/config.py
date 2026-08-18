import os
from dotenv import load_dotenv

load_dotenv()

class BaseConfig:
    """Base configuration — shared across all environments."""

    # Security
    SECRET_KEY = os.getenv("SECRET_KEY", None)
    if not SECRET_KEY:
        raise ValueError("SECRET_KEY environment variable is not set.")

    # SQLAlchemy
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Session
    PERMANENT_SESSION_LIFETIME_HOURS = 8

    # Stripe
    STRIPE_PUBLIC_KEY  = os.getenv("STRIPE_PUBLIC_KEY")
    STRIPE_SECRET_KEY  = os.getenv("STRIPE_SECRET_KEY")

    # Geocoding
    ORS_API_KEY = os.getenv("ORS_API_KEY")

    # Mail
    MAIL_SERVER         = "smtp.gmail.com"
    MAIL_PORT           = 587
    MAIL_USE_TLS        = True
    MAIL_USE_SSL        = False
    MAIL_USERNAME       = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD       = os.getenv("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_USERNAME")

    # Database
    DB_HOST     = os.getenv("DB_HOST", "localhost")
    DB_USER     = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_NAME     = os.getenv("DB_NAME", "reservations_restaurant_db")

    # Geocoding
    ORS_API_KEY = os.getenv("ORS_API_KEY")

    @classmethod
    def get_db_uri(cls):
        return (
            f"mysql+mysqlconnector://{cls.DB_USER}:{cls.DB_PASSWORD}"
            f"@{cls.DB_HOST}/{cls.DB_NAME}"
        )


class DevelopmentConfig(BaseConfig):
    """Development — debug on, verbose errors."""
    DEBUG   = True
    TESTING = False
    SQLALCHEMY_DATABASE_URI = BaseConfig.get_db_uri()
    SQLALCHEMY_ECHO = True


class ProductionConfig(BaseConfig):
    """Production — debug off, no SQL logging."""
    DEBUG   = False
    TESTING = False
    SQLALCHEMY_DATABASE_URI = BaseConfig.get_db_uri()
    SQLALCHEMY_ECHO = False


class TestingConfig(BaseConfig):
    """Testing — uses SQLite in memory, no MySQL needed."""
    DEBUG   = True
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_ECHO = False


# This maps string names to config classes — used in create_app()
config_map = {
    "development": DevelopmentConfig,
    "production":  ProductionConfig,
    "testing":     TestingConfig,
}


def get_config():
    """Returns the correct config class based on FLASK_ENV env var."""
    env = os.getenv("FLASK_ENV", "development").lower()
    cfg = config_map.get(env, DevelopmentConfig)
    return cfg