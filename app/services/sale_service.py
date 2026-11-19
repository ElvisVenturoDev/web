"""Sale service: sale header and product line registration."""

from datetime import date

from app.database import db
from app.models import Sale, SaleDetail


def create_sale(
    customer_id,
    delivery_type,
    delivery_address,
    district,
    comments,
):
    """Register a sale header associated with a customer.

    Args:
        customer_id (int): Customer identifier.
        delivery_type (str): Delivery type (``home_delivery`` or ``pickup``).
        delivery_address (str): Delivery address or method.
        district (str | None): Delivery district.
        comments (str | None): Order comments.

    Returns:
        Sale: Sale added to the session with its identifier assigned.
    """
    sale = Sale(
        date_of_sale=date.today(),
        customer_id=customer_id,
        delivery_type=delivery_type,
        delivery_address=delivery_address,
        district=district,
        comments=comments,
    )
    db.session.add(sale)
    db.session.flush()
    return sale


def add_sale_detail(sale_id, product, quantity):
    """Add a product line to a sale.

    Args:
        sale_id (int): Sale identifier.
        product (Product): Sold product.
        quantity (int): Sold quantity.

    Returns:
        SaleDetail: Line added to the session.
    """
    detail = SaleDetail(
        sale_id=sale_id,
        product_id=product.id,
        quantity=quantity,
        unit_price=product.price,
    )
    db.session.add(detail)
    return detail
