"""Startup diagnostics for production (Amvera logs are read from stderr)."""

from __future__ import annotations

import os
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from flask import Flask

STARTUP_LOG_PREFIX = "startup"

REQUIRED_ENV_KEYS: tuple[str, ...] = (
    "FLASK_SECRET_KEY",
    "ADMIN_USERNAME",
    "ADMIN_PASSWORD",
)

OPTIONAL_ENV_KEYS: tuple[str, ...] = (
    "DATABASE_URL",
    "TIMEZONE",
    "SITE_ADDRESS",
    "SITE_PHONE",
    "PORT",
    "FLASK_DEBUG",
)


def log_startup(message: str) -> None:
    """
    Write one line to stderr (visible in Amvera application/system logs).

    Args:
        message: Human-readable detail without secrets.
    """
    print(f"{STARTUP_LOG_PREFIX}: {message}", file=sys.stderr, flush=True)


def log_runtime_context() -> None:
    """Log interpreter and working directory (helps catch wrong container layout)."""
    log_startup(f"Python {sys.version.split()[0]} pid={os.getpid()}")
    log_startup(f"cwd={os.getcwd()}")


def log_environment_presence() -> list[str]:
    """
    Mark which env vars are set (never print secret values).

    Returns:
        Names of required variables that are missing or empty.
    """
    missing_required: list[str] = []
    for key in REQUIRED_ENV_KEYS:
        if os.getenv(key, "").strip():
            log_startup(f"env {key}=set")
        else:
            log_startup(f"env {key}=MISSING")
            missing_required.append(key)

    for key in OPTIONAL_ENV_KEYS:
        raw = os.getenv(key, "")
        if raw.strip():
            if key == "DATABASE_URL":
                log_startup(f"env {key}=set ({describe_database_url(raw)})")
            else:
                log_startup(f"env {key}=set (len={len(raw)})")
        else:
            log_startup(f"env {key}=default-or-empty")

    return missing_required


def describe_database_url(database_url: str) -> str:
    """
    Summarize ``DATABASE_URL`` without leaking credentials (SQLite only).

    Args:
        database_url: Raw value from the environment.
    """
    if database_url.startswith("sqlite:"):
        if ":memory:" in database_url:
            return "sqlite in-memory"
        if database_url.startswith("sqlite:////"):
            return f"sqlite file {database_url.removeprefix('sqlite:')}"
        return "sqlite file (relative or resolved at runtime)"
    return f"non-sqlite scheme ({database_url.split(':', 1)[0]})"


def log_application_config(flask_app: Flask) -> None:
    """Log resolved app settings safe for operators (no passwords)."""
    log_startup(f"config TIMEZONE={flask_app.config.get('TIMEZONE')}")
    log_startup(
        f"config ADMIN_USERNAME={'set' if flask_app.config.get('ADMIN_USERNAME') else 'MISSING'}"
    )
    log_startup(
        f"config SQLALCHEMY_DATABASE_URI={describe_database_url(flask_app.config['SQLALCHEMY_DATABASE_URI'])}"
    )


def log_database_schema(flask_app: Flask) -> None:
    """Confirm tables exist after ``create_all`` / init."""
    from sqlalchemy import inspect, text

    from app.extensions import db

    with flask_app.app_context():
        inspector = inspect(db.engine)
        tables = sorted(inspector.get_table_names())
        log_startup(f"database tables={tables if tables else '(none)'}")
        if "booking" in tables:
            count = db.session.execute(text("SELECT COUNT(*) FROM booking")).scalar_one()
            log_startup(f"database booking rows={count}")
        else:
            log_startup("database booking table MISSING after schema init")


def log_fatal(exc: BaseException, *, phase: str) -> None:
    """
    Log exception type and message before re-raising upstream.

    Args:
        exc: Caught error.
        phase: Short stage name (e.g. ``db_init``, ``wsgi``).
    """
    log_startup(f"FAILED phase={phase} error={type(exc).__name__}: {exc}")