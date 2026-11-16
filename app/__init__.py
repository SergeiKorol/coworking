"""Application factory."""

from flask import Flask

from app.config import BaseConfig, TestingConfig, resolve_database_url
from app.extensions import csrf, db, migrate


def create_app(config_name: str | None = None) -> Flask:
    """
    Create and configure the Flask application.

    Args:
        config_name: Pass ``\"testing\"`` for the pytest configuration.
    """
    flask_app = Flask(__name__, instance_relative_config=True)

    if config_name == "testing":
        flask_app.config.from_object(TestingConfig)
    else:
        flask_app.config.from_object(BaseConfig)
        flask_app.config["SQLALCHEMY_DATABASE_URI"] = resolve_database_url(
            flask_app.config["SQLALCHEMY_DATABASE_URI"]
        )
        missing = [
            key
            for key, value in (
                ("FLASK_SECRET_KEY", flask_app.config["SECRET_KEY"]),
                ("ADMIN_USERNAME", flask_app.config["ADMIN_USERNAME"]),
                ("ADMIN_PASSWORD", flask_app.config["ADMIN_PASSWORD"]),
            )
            if not value
        ]
        if missing:
            raise RuntimeError(
                f"Missing required environment variables: {', '.join(missing)}"
            )

    db.init_app(flask_app)
    migrate.init_app(flask_app, db)
    csrf.init_app(flask_app)

    from app.blueprints.admin import admin_bp
    from app.blueprints.public import public_bp

    flask_app.register_blueprint(public_bp)
    flask_app.register_blueprint(admin_bp)

    @flask_app.context_processor
    def inject_site_content() -> dict[str, str]:
        """Expose contact details to public templates."""
        return {
            "site_address": flask_app.config["SITE_ADDRESS"],
            "site_phone": flask_app.config["SITE_PHONE"],
        }

    import app.models  # noqa: F401

    return flask_app
