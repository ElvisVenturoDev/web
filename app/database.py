"""Centralized Flask-SQLAlchemy initialization."""

from contextlib import contextmanager

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError, OperationalError, SQLAlchemyError

db = SQLAlchemy()

# Avoid dead connections when MySQL closes idle sessions. Shared by both
# clients: the Flask web app and the JavaFX desktop app.
DEFAULT_ENGINE_OPTIONS = {
    "pool_pre_ping": True,
    "pool_recycle": 280,
    "pool_size": 10,
    "max_overflow": 20,
}


class DatabaseUnavailableError(Exception):
    """The database is unreachable or locked."""


class DatabaseWriteError(Exception):
    """The database rejected or could not complete a write."""


@contextmanager
def transaction():
    """Run a block inside the current session transaction.

    Commits on success. On failure it rolls back and translates SQLAlchemy
    errors into application exceptions.
    """
    try:
        yield db.session
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise
    except OperationalError as error:
        db.session.rollback()
        raise DatabaseUnavailableError from error
    except SQLAlchemyError as error:
        db.session.rollback()
        raise DatabaseWriteError from error
    except ValueError:
        db.session.rollback()
        raise


def init_app(app):
    """Register Flask-SQLAlchemy in the application.

    The schema is managed exclusively by Alembic migrations; ``create_all`` is
    intentionally not used here.
    """
    app.config.setdefault("SQLALCHEMY_DATABASE_URI", app.config["DATABASE_URL"])
    options = dict(DEFAULT_ENGINE_OPTIONS)
    if app.config["SQLALCHEMY_DATABASE_URI"].startswith("mysql+pymysql"):
        options["connect_args"] = {"init_command": "SET time_zone = '-05:00'"}
    app.config.setdefault("SQLALCHEMY_ENGINE_OPTIONS", options)
    app.config.setdefault("SQLALCHEMY_TRACK_MODIFICATIONS", False)
    db.init_app(app)
