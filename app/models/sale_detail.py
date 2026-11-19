"""Sale detail model."""

from app.database import db


class SaleDetail(db.Model):
    """Product line of a sale (table ``sale_details``)."""

    __tablename__ = "sale_details"

    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(
        db.Integer,
        db.ForeignKey("sales.id"),
        nullable=False,
    )
    product_id = db.Column(
        db.Integer,
        db.ForeignKey("products.id"),
        nullable=False,
    )
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)

    sale = db.relationship("Sale", back_populates="details")
    product = db.relationship("Product")
