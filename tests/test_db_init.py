"""Tests for Amvera-style SQLite reset on container start."""

from datetime import datetime

from sqlalchemy import func, inspect, select

from app import create_app
from app.db_init import reset_sqlite_and_create_schema
from app.extensions import db
from app.models import Booking


def test_reset_sqlite_and_create_schema_wipes_rows(tmp_path, monkeypatch) -> None:
    """Each prestart must drop file and recreate empty booking table."""
    db_file = tmp_path / "coworking.db"
    monkeypatch.setenv("FLASK_SECRET_KEY", "test-secret-key")
    monkeypatch.setenv("ADMIN_USERNAME", "admin")
    monkeypatch.setenv("ADMIN_PASSWORD", "test-password")
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_file.as_posix()}")

    app = create_app()
    with app.app_context():
        db.create_all()
        db.session.add(
            Booking(
                unit_id="desk-1",
                starts_at=datetime(2026, 1, 1, 9, 0),
                ends_at=datetime(2026, 1, 1, 18, 0),
            )
        )
        db.session.commit()
        count_before = db.session.scalar(select(func.count()).select_from(Booking))
        assert count_before == 1, "seed row must exist"

        reset_sqlite_and_create_schema()
        tables = set(inspect(db.engine).get_table_names())
        assert "booking" in tables, "booking table must exist after recreate"
        count_after = db.session.scalar(select(func.count()).select_from(Booking))
        assert count_after == 0, "restart must yield empty database"