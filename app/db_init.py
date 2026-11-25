"""Reset SQLite and create tables without Alembic (simple Amvera deploy)."""

from __future__ import annotations

import sys
from pathlib import Path

from flask import current_app

from app import create_app
from app.extensions import db


def sqlite_path_from_uri(database_uri: str) -> Path | None:
    """
    Return filesystem path for a SQLite URI, or None if not file-backed SQLite.

    Args:
        database_uri: Value of ``SQLALCHEMY_DATABASE_URI`` after resolution.
    """
    prefix = "sqlite:///"
    if not database_uri.startswith(prefix):
        return None
    rest = database_uri[len(prefix) :]
    if rest == ":memory:":
        return None
    if rest.startswith("/"):
        return Path(rest)
    return Path(rest).resolve()


def reset_sqlite_and_create_schema() -> None:
    """
    Delete the SQLite file when present, then create tables via SQLAlchemy.

    Each container start gets an empty database — no Flask-Migrate on Amvera.
    """
    uri = current_app.config["SQLALCHEMY_DATABASE_URI"]
    db_path = sqlite_path_from_uri(uri)
    db.session.remove()
    db.engine.dispose()
    if db_path is not None:
        if db_path.exists():
            db_path.unlink()
            print(f"db_init: removed {db_path}", file=sys.stderr)
        db_path.parent.mkdir(parents=True, exist_ok=True)
    db.create_all()


def main() -> None:
    """CLI entry for deploy prestart (``python -m app.db_init``)."""
    flask_app = create_app()
    with flask_app.app_context():
        reset_sqlite_and_create_schema()
    print("db_init: empty schema ready.", file=sys.stderr)


if __name__ == "__main__":
    main()