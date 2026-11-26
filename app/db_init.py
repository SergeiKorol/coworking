"""Reset SQLite and create tables without Alembic (simple Amvera deploy)."""

from __future__ import annotations

import os
from pathlib import Path

from flask import current_app

from app import create_app
from app.extensions import db
from app.startup_log import (
    log_application_config,
    log_database_schema,
    log_environment_presence,
    log_fatal,
    log_runtime_context,
    log_startup,
)


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
        parent_writable = _log_path_access(db_path)
        log_startup(
            f"database target path={db_path} parent_writable={parent_writable}"
        )
        if db_path.exists():
            db_path.unlink()
            log_startup(f"database removed existing file at {db_path}")
        db_path.parent.mkdir(parents=True, exist_ok=True)
    else:
        log_startup(f"database uri={uri} (not a file-backed sqlite path)")
    db.create_all()
    log_startup("database create_all() finished")


def _log_path_access(db_path: Path) -> bool:
    """Return whether the parent directory exists or can be created."""
    parent = db_path.parent
    if parent.exists():
        return os.access(parent, os.W_OK)  # type: ignore[name-defined]
    try:
        parent.mkdir(parents=True, exist_ok=True)
        return os.access(parent, os.W_OK)  # type: ignore[name-defined]
    except OSError:
        return False


def main() -> None:
    """CLI entry for deploy prestart (``python -m app.db_init``)."""
    log_startup("phase=db_init begin")
    log_runtime_context()
    missing = log_environment_presence()
    if missing:
        msg = f"required env missing: {', '.join(missing)}"
        log_startup(msg)
        raise RuntimeError(msg)

    try:
        flask_app = create_app()
        log_application_config(flask_app)
        with flask_app.app_context():
            reset_sqlite_and_create_schema()
        log_database_schema(flask_app)
        log_startup("phase=db_init complete — schema ready")
    except Exception as exc:
        log_fatal(exc, phase="db_init")
        raise


if __name__ == "__main__":
    main()