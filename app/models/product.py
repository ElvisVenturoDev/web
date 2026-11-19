"""Product model."""

from app.constants import (
    CATEGORY_FALLBACK,
    PRODUCT_CATEGORY_MAX_LENGTH,
    PRODUCT_DETAIL_MAX_LENGTH,
    PRODUCT_IMAGE_URL_MAX_LENGTH,
    PRODUCT_NAME_MAX_LENGTH,
)
from app.database import db


class Product(db.Model):
    """Catalog product (table ``products``)."""

    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(PRODUCT_NAME_MAX_LENGTH), nullable=False, unique=True)
    category = db.Column(
        db.String(PRODUCT_CATEGORY_MAX_LENGTH),
        nullable=False,
        default=CATEGORY_FALLBACK,
    )
    detail = db.Column(db.String(PRODUCT_DETAIL_MAX_LENGTH))
    description = db.Column(db.Text)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    image_url = db.Column(db.String(PRODUCT_IMAGE_URL_MAX_LENGTH))
    active = db.Column(db.Boolean, nullable=False, default=True)

    inventory = db.relationship("Inventory", back_populates="product", uselist=False)
