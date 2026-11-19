"""Inventory service: stock lookup and discount per product."""

from app.constants import DEFAULT_MIN_STOCK
from app.database import db
from app.models import Inventory


def get_or_create_inventory(product_id):
    """Get a product inventory row, creating it at zero when missing.

    Locks the row to update stock safely inside the current transaction.

    Args:
        product_id (int): Product identifier.

    Returns:
        Inventory: Inventory associated with the product.
    """
    inventory = db.session.scalars(
        db.select(Inventory)
        .filter_by(product_id=product_id)
        .with_for_update()
        .limit(1)
    ).first()
    if inventory is None:
        inventory = Inventory(
            product_id=product_id,
            stock=0,
            min_stock=DEFAULT_MIN_STOCK,
        )
        db.session.add(inventory)
    return inventory


def discount_stock(product_id, quantity):
    """Discount units from a product stock when enough units are available.

    Args:
        product_id (int): Product identifier.
        quantity (int): Quantity requested by the order.

    Returns:
        Inventory: Updated inventory (created at zero when missing).
    """
    inventory = get_or_create_inventory(product_id)
    if inventory.stock >= quantity:
        inventory.stock -= quantity
    return inventory
