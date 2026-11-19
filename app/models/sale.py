"""Sale model."""

from datetime import date

from app.constants import (
    ADDRESS_MAX_LENGTH,
    COMMENTS_MAX_LENGTH,
    DELIVERY_TYPE_MAX_LENGTH,
    DISTRICT_MAX_LENGTH,
    SALE_CHANNEL_MAX_LENGTH,
    SALE_CHANNEL_WEB,
    SALE_STATUS_MAX_LENGTH,
    SALE_STATUS_PENDING,
)
from app.database import db


class Sale(db.Model):
    """Order registered from the website (table ``sales``)."""

    __tablename__ = "sales"

    id = db.Column(db.Integer, primary_key=True)
    date_of_sale = db.Column(db.Date, nullable=False, default=date.today)
    customer_id = db.Column(
        db.Integer,
        db.ForeignKey("customers.id"),
        nullable=False,
    )
    delivery_type = db.Column(db.String(DELIVERY_TYPE_MAX_LENGTH), nullable=False)
    delivery_address = db.Column(db.String(ADDRESS_MAX_LENGTH), nullable=False)
    district = db.Column(db.String(DISTRICT_MAX_LENGTH))
    comments = db.Column(db.String(COMMENTS_MAX_LENGTH))
    status = db.Column(
        db.String(SALE_STATUS_MAX_LENGTH),
        nullable=False,
        default=SALE_STATUS_PENDING,
    )
    channel = db.Column(
        db.String(SALE_CHANNEL_MAX_LENGTH),
        nullable=False,
        default=SALE_CHANNEL_WEB,
    )

    customer = db.relationship("Customer", back_populates="sales")
    details = db.relationship("SaleDetail", back_populates="sale")
