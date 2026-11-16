"""Application configuration classes."""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def resolve_database_url(database_url: str) -> str:
    """
    Turn relative SQLite paths into absolute URIs (reliable on Windows + Flask).
    """
    prefix = "sqlite:///"
    if not database_url.startswith(prefix):
        return database_url
    rest = database_url[len(prefix) :]
    # Already absolute on Windows (D:/...) or Unix (//...)
    if rest.startswith("/") or (len(rest) > 1 and rest[1] == ":"):
        return database_url
    absolute = (BASE_DIR / rest).resolve().as_posix()
    return f"{prefix}{absolute}"


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
    SITE_ADDRESS = os.getenv(
        "SITE_ADDRESS",
        "Кострома, ул. Маршала Новикова, 1",
    )
    SITE_PHONE = os.getenv("SITE_PHONE", "+7 494 230-15-95")


class TestingConfig(BaseConfig):
    """In-memory SQLite and disabled CSRF for pytest."""

    TESTING = True
    SECRET_KEY = "test-secret-key"
    ADMIN_USERNAME = "admin"
    ADMIN_PASSWORD = "test-password"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False
