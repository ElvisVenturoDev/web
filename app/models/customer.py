"""Customer model."""

from app.database import db
from app.constants import (
    EMAIL_MAX_LENGTH,
    NAME_MAX_LENGTH,
    PASSWORD_HASH_MAX_LENGTH,
    PHONE_MAX_LENGTH,
)


class Customer(db.Model):
    """Store customer (table ``customers``)."""

    __tablename__ = "customers"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(NAME_MAX_LENGTH), nullable=False)
    phone = db.Column(db.String(PHONE_MAX_LENGTH))
    email = db.Column(db.String(EMAIL_MAX_LENGTH), unique=True)
    password_hash = db.Column(db.String(PASSWORD_HASH_MAX_LENGTH))
    active = db.Column(db.Boolean, nullable=False, default=True)

    detail = db.relationship(
        "CustomerDetail", back_populates="customer", uselist=False
    )
    sales = db.relationship("Sale", back_populates="customer")
