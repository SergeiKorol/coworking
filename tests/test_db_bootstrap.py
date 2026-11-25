"""Tests for production database bootstrap before gunicorn."""

from sqlalchemy import inspect

from app import create_app
from app.db_bootstrap import ensure_database_schema
from app.extensions import db


def test_ensure_database_schema_stamps_after_create_all(
    tmp_path, monkeypatch
) -> None:
    """If create_all ran first, bootstrap must not block deploy on upgrade conflict."""
    db_file = tmp_path / "coworking.db"
    monkeypatch.setenv("FLASK_SECRET_KEY", "test-secret-key")
    monkeypatch.setenv("ADMIN_USERNAME", "admin")
    monkeypatch.setenv("ADMIN_PASSWORD", "test-password")
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_file.as_posix()}")

    app = create_app()
    with app.app_context():
        db.create_all()
        ensure_database_schema()
        tables = set(inspect(db.engine).get_table_names())
        assert "booking" in tables, "booking table must exist"
        assert "alembic_version" in tables, (
            "Alembic must be stamped after create_all reconciliation"
        )