"""One-shot database schema setup before gunicorn workers start."""

from __future__ import annotations

import sys

from app import create_app
from app.extensions import db


def ensure_database_schema() -> None:
    """
    Apply Alembic migrations on a fresh SQLite file.

    If the database was created earlier via ``db.create_all()`` (no
    ``alembic_version`` row), stamp the current head instead of failing on
    "table already exists". That keeps Amvera startup from blocking gunicorn.
    """
    from flask_migrate import stamp, upgrade
    from sqlalchemy import inspect

    inspector = inspect(db.engine)
    tables = set(inspector.get_table_names())

    if "booking" in tables and "alembic_version" not in tables:
        print(
            "db_bootstrap: booking table without Alembic history; stamping head.",
            file=sys.stderr,
        )
        stamp(revision="head")
        return

    try:
        upgrade()
    except Exception as exc:
        message = str(exc).lower()
        if "booking" in tables and "already exists" in message:
            print(
                "db_bootstrap: migration conflict on existing booking; stamping head.",
                file=sys.stderr,
            )
            stamp(revision="head")
            return
        raise


def main() -> None:
    """CLI entry point for deploy prestart (``python -m app.db_bootstrap``)."""
    flask_app = create_app()
    with flask_app.app_context():
        ensure_database_schema()
    print("db_bootstrap: schema ready.", file=sys.stderr)


if __name__ == "__main__":
    main()