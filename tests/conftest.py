"""Pytest fixtures."""

import pytest
from sqlalchemy.pool import StaticPool

from app import create_app
from app.extensions import db


@pytest.fixture
def flask_app():
    """Application with in-memory database."""
    application = create_app("testing")
    application.config.update(
        SQLALCHEMY_ENGINE_OPTIONS={
            "poolclass": StaticPool,
            "connect_args": {"check_same_thread": False},
        }
    )
    with application.app_context():
        db.create_all()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(flask_app):
    """Flask test client."""
    return flask_app.test_client()
