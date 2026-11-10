"""Application configuration classes."""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


class BaseConfig:
    """Production-like settings loaded from environment variables."""

    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{(BASE_DIR / 'instance' / 'coworking.db').as_posix()}",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TIMEZONE = os.getenv("TIMEZONE", "Europe/Moscow")
    ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")
    WTF_CSRF_ENABLED = True


class TestingConfig(BaseConfig):
    """In-memory SQLite and disabled CSRF for pytest."""

    TESTING = True
    SECRET_KEY = "test-secret-key"
    ADMIN_USERNAME = "admin"
    ADMIN_PASSWORD = "test-password"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False
