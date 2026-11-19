"""Shared model helpers: identifiers and timestamp columns."""

from sqlalchemy.dialects import mysql

from app.database import db
from app.timeutil import now_lima


def BigInt():
    """Big integer compatible with BIGINT UNSIGNED in MySQL and INTEGER in tests."""
    return (
        db.BigInteger()
        .with_variant(mysql.BIGINT(unsigned=True), "mysql")
        .with_variant(db.Integer(), "sqlite")
    )


class TimestampMixin:
    """Creation and update timestamps stored in America/Lima time."""

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=now_lima,
        server_default=db.func.current_timestamp(),
    )
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=now_lima,
        onupdate=now_lima,
        server_default=db.func.current_timestamp(),
    )
