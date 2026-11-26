"""WSGI entry point for production hosts (Amvera, PythonAnywhere, HelioHost, Replit)."""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

from app import create_app
from app.startup_log import log_environment_presence, log_fatal, log_startup

log_startup("phase=wsgi loading application")
_missing = log_environment_presence()

try:
    app = create_app()
except Exception as exc:
    log_fatal(exc, phase="wsgi")
    raise

if _missing:
    log_startup(
        f"wsgi: warning — required env was missing at import: {', '.join(_missing)}"
    )
else:
    log_startup("phase=wsgi application object created")


def main() -> None:
    """
    Start a built-in HTTP server (Replit workflow / ``python wsgi.py``).

    PythonAnywhere and similar hosts import ``app`` only and do not call this.
    """
    instance_dir = Path(__file__).resolve().parent / "instance"
    instance_dir.mkdir(parents=True, exist_ok=True)

    port = int(os.environ.get("PORT", "5000"))
    debug = os.environ.get("FLASK_DEBUG", "").lower() in ("1", "true", "yes")
    app.run(host="0.0.0.0", port=port, debug=debug)


if __name__ == "__main__":
    main()