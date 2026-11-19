"""Inventory model."""

from app.constants import DEFAULT_MIN_STOCK
from app.database import db


class Inventory(db.Model):
    """Product stock (table ``inventory``)."""

    __tablename__ = "inventory"

    product_id = db.Column(
        db.Integer,
        db.ForeignKey("products.id"),
        primary_key=True,
    )
    stock = db.Column(db.Integer, nullable=False, default=0)
    min_stock = db.Column(db.Integer, nullable=False, default=DEFAULT_MIN_STOCK)

    product = db.relationship("Product", back_populates="inventory")
