"""Tests for startup diagnostics (no secrets in messages)."""

from app.startup_log import (
    REQUIRED_ENV_KEYS,
    describe_database_url,
    log_environment_presence,
)


def test_log_environment_presence_reports_missing_required(
    monkeypatch, capsys
) -> None:
    """Missing secrets must be reported as MISSING without printing values."""
    for key in REQUIRED_ENV_KEYS:
        monkeypatch.delenv(key, raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)

    missing = log_environment_presence()
    captured = capsys.readouterr().err

    assert missing == list(REQUIRED_ENV_KEYS), "all required keys should be missing"
    assert "MISSING" in captured, "stderr must flag missing vars"
    assert "change-me" not in captured.lower()


def test_describe_database_url_hides_credentials() -> None:
    """Non-SQLite URLs must not echo passwords in summaries."""
    assert "postgresql" in describe_database_url(
        "postgresql://user:secret@host/db"
    )
    assert "secret" not in describe_database_url(
        "postgresql://user:secret@host/db"
    )


def test_describe_database_url_sqlite_file() -> None:
    """SQLite paths are safe to show for operators."""
    summary = describe_database_url("sqlite:////app/instance/coworking.db")
    assert "instance" in summary