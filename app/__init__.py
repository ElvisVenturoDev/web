"""Flask application factory for the Miramar hotel platform."""

import os
from datetime import timedelta

from flask import Flask, jsonify, render_template, send_from_directory

from app import database
from app import models  # noqa: F401  (register models with Alembic)
from app.config import (
    get_database_uri,
    get_idle_minutes,
    get_secret_key,
    get_timezone_name,
    is_production,
)
from app.extensions import csrf, limiter, migrate
from app.timeutil import now_lima


def _register_blueprints(app):
    """Register the public site and the administrative panel."""
    from app.routes.admin import ADMIN_BP
    from app.routes.contact import CONTACT_BP
    from app.routes.home import HOME_BP
    from app.routes.products import PRODUCTS_BP

    app.register_blueprint(HOME_BP)
    app.register_blueprint(PRODUCTS_BP)
    app.register_blueprint(CONTACT_BP)
    app.register_blueprint(ADMIN_BP, url_prefix="/admin")


def _register_sitemap(app):
    @app.get("/sitemap.xml")
    def serve_sitemap():
        return send_from_directory(
            os.path.dirname(app.root_path), "sitemap.xml", mimetype="application/xml"
        )


def _register_security_headers(app):
    @app.after_request
    def add_security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'self'; "
            "img-src 'self' data: https:; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com data:; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "frame-src https://www.openstreetmap.org; "
            "connect-src 'self'; "
            "base-uri 'self'; form-action 'self';",
        )
        response.headers.setdefault(
            "Permissions-Policy", "geolocation=(), microphone=(), camera=()"
        )
        return response


def _register_template_helpers(app):
    @app.template_filter("money")
    def money_filter(value):
        try:
            return f"S/ {float(value or 0):,.2f}"
        except (TypeError, ValueError):
            return "S/ 0.00"

    @app.template_filter("date_pe")
    def date_pe_filter(value):
        return value.strftime("%d/%m/%Y") if value else "—"

    @app.template_filter("datetime_pe")
    def datetime_pe_filter(value):
        return value.strftime("%d/%m/%Y %H:%M") if value else "—"

    @app.template_filter("nights")
    def nights_filter(value):
        return value.nights if value else 0

    @app.context_processor
    def inject_globals():
        return {"current_year": now_lima().year}


def _register_error_handlers(app):
    @app.errorhandler(404)
    def not_found(error):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(error):
        database.db.session.rollback()
        return render_template("errors/500.html"), 500

    @app.errorhandler(413)
    def too_large(error):
        return jsonify({"error": "El archivo supera el tamaño máximo permitido."}), 413


def create_app(test_config=None):
    """Create and configure the Flask application.

    Args:
        test_config (dict | None): Configuration overriding the defaults,
            useful in tests.

    Returns:
        Flask: Application ready to run.
    """
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=get_secret_key(),
        DATABASE_URL=get_database_uri(),
        TIMEZONE=get_timezone_name(),
        ADMIN_IDLE_MINUTES=get_idle_minutes(),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=is_production(),
        PERMANENT_SESSION_LIFETIME=timedelta(hours=8),
        MAX_CONTENT_LENGTH=8 * 1024 * 1024,
        WTF_CSRF_TIME_LIMIT=None,
        RATELIMIT_STORAGE_URI="memory://",
    )

    if test_config:
        app.config.update(test_config)
        if test_config.get("SQLALCHEMY_DATABASE_URI") and not test_config.get(
            "DATABASE_URL"
        ):
            app.config["DATABASE_URL"] = test_config["SQLALCHEMY_DATABASE_URI"]

    database.init_app(app)
    csrf.init_app(app)
    migrate.init_app(app, database.db, render_as_batch=True)
    limiter.init_app(app)

    _register_blueprints(app)
    _register_sitemap(app)
    _register_security_headers(app)
    _register_template_helpers(app)
    _register_error_handlers(app)

    from app.cli import register_cli

    register_cli(app)

    return app
