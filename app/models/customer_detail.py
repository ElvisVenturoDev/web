"""Customer detail model."""

from datetime import date, datetime

from app.constants import (
    ADDRESS_MAX_LENGTH,
    CUSTOMER_TYPE_MAX_LENGTH,
    CUSTOMER_TYPE_RETAIL,
    DISTRICT_MAX_LENGTH,
)
from app.database import db


class CustomerDetail(db.Model):
    """Customer address and type (table ``customer_details``)."""

    __tablename__ = "customer_details"

    customer_id = db.Column(
        db.Integer,
        db.ForeignKey("customers.id"),
        primary_key=True,
    )
    address = db.Column(db.String(ADDRESS_MAX_LENGTH), nullable=False)
    district = db.Column(db.String(DISTRICT_MAX_LENGTH))
    customer_type = db.Column(
        db.String(CUSTOMER_TYPE_MAX_LENGTH),
        nullable=False,
        default=CUSTOMER_TYPE_RETAIL,
    )
    registered_on = db.Column(db.Date, nullable=False, default=date.today)
    updated_at = db.Column(
        db.DateTime, default=datetime.now, onupdate=datetime.now
    )

    customer = db.relationship("Customer", back_populates="detail")
