"""Centralized application configuration from environment variables."""

import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:  # Without python-dotenv only system variables are used.
    load_dotenv = None

if load_dotenv is not None:
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")


DEFAULT_SECRET_KEY = "dev-secret-key-miramar"
DEFAULT_PORT = 5000
DEFAULT_TIMEZONE = "America/Lima"


def get_env(name, default=None):
    """Read an environment variable and fail clearly when it is missing."""
    value = os.environ.get(name, default)
    if value is None or value == "":
        raise RuntimeError(
            f"Falta la variable de entorno {name}. Revisa tu archivo .env "
            "(usa .env.example como plantilla)."
        )
    return value


def get_secret_key():
    """Return the Flask secret key."""
    return os.environ.get("SECRET_KEY", DEFAULT_SECRET_KEY)


def get_port():
    """Return the application port."""
    return int(os.environ.get("PORT", DEFAULT_PORT))


def get_database_uri():
    """Return the shared MySQL connection string.

    The database is the single source of truth for the web application and the
    future JavaFX desktop client. There is intentionally no SQLite fallback in
    this phase; the application must fail clearly when ``DATABASE_URL`` is not
    configured.
    """
    return get_env("DATABASE_URL")


def get_timezone_name():
    """Return the business timezone name."""
    return os.environ.get("TIMEZONE", DEFAULT_TIMEZONE)


def get_idle_minutes():
    """Return the admin session inactivity limit in minutes."""
    try:
        return max(1, int(os.environ.get("ADMIN_IDLE_MINUTES", "30")))
    except ValueError:
        return 30


def is_production():
    """Whether the app runs in production mode."""
    return os.environ.get("FLASK_ENV", "development").lower() == "production"


def get_admin_seed():
    """Return the initial administrator values used by the seed command."""
    return {
        "name": os.environ.get("ADMIN_SEED_NAME", "Administrador"),
        "email": os.environ.get("ADMIN_SEED_EMAIL", "admin@miramarhotel.pe"),
        "password": os.environ.get("ADMIN_SEED_PASSWORD", ""),
    }
