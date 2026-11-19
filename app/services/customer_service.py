"""Customer service: lookup and registration for the order customer."""

from dataclasses import dataclass
from datetime import date, datetime

from sqlalchemy import case, or_

from app.constants import CUSTOMER_TYPE_RETAIL
from app.database import db
from app.models import Customer, CustomerDetail


@dataclass
class OrderCustomerData:
    """Customer values collected by the order form.

    Attributes:
        name (str): Normalized customer name.
        phone (str): Customer phone number.
        email (str | None): Normalized email.
        detail_address (str): Customer-detail address.
        detail_district (str | None): Customer-detail district.
        update_address (bool): Whether to overwrite the stored address.
    """

    name: str
    phone: str
    email: str | None
    detail_address: str
    detail_district: str | None
    update_address: bool = False


def find_order_customer(email, phone):
    """Find the customer of an order by email or phone.

    Args:
        email (str | None): Order email (may be ``None``).
        phone (str): Order phone number.

    Returns:
        Customer | None: Found customer; when several match, prefers the email
        match.
    """
    conditions = [Customer.phone == phone]
    ordering = [Customer.id]
    if email:
        conditions.append(Customer.email == email)
        ordering.insert(0, case((Customer.email == email, 0), else_=1))
    return db.session.scalars(
        db.select(Customer).where(or_(*conditions)).order_by(*ordering).limit(1)
    ).first()


def save_customer_detail(customer_id, address, district, update_existing):
    """Insert or update a customer address detail.

    Args:
        customer_id (int): Customer identifier.
        address (str): Address to save.
        district (str | None): District to save.
        update_existing (bool): Whether to overwrite an existing address and
            district.

    Returns:
        None: The detail row is inserted or updated in the current session.
    """
    detail = db.session.get(CustomerDetail, customer_id)
    if detail is None:
        db.session.add(
            CustomerDetail(
                customer_id=customer_id,
                address=address,
                district=district,
                customer_type=CUSTOMER_TYPE_RETAIL,
                registered_on=date.today(),
            )
        )
    elif update_existing:
        detail.address = address
        detail.district = district
        detail.customer_type = CUSTOMER_TYPE_RETAIL
    else:
        detail.updated_at = datetime.now()


def _update_order_customer(customer, customer_data):
    """Update an existing customer with the order data.

    Args:
        customer (Customer): Customer to update.
        customer_data (OrderCustomerData): Customer values from the order form.

    Returns:
        Customer: Updated customer.
    """
    customer.name = customer_data.name
    customer.phone = customer_data.phone
    if customer.email is None:
        customer.email = customer_data.email
    save_customer_detail(
        customer.id,
        customer_data.detail_address,
        customer_data.detail_district,
        update_existing=customer_data.update_address,
    )
    return customer


def _create_order_customer(customer_data):
    """Create the customer and detail rows for a new order.

    Args:
        customer_data (OrderCustomerData): Customer values from the order form.

    Returns:
        Customer: Created customer.
    """
    # Orders may create the customer before /registro sets a password.
    customer = Customer(
        name=customer_data.name,
        phone=customer_data.phone,
        email=customer_data.email,
        password_hash="",
    )
    db.session.add(customer)
    db.session.flush()
    save_customer_detail(
        customer.id,
        customer_data.detail_address,
        customer_data.detail_district,
        update_existing=False,
    )
    return customer


def get_or_create_order_customer(customer_data):
    """Find or create the customer placing an order and update their detail.

    Args:
        customer_data (OrderCustomerData): Customer values from the order form.

    Returns:
        Customer: Found or created customer.

    Raises:
        ValueError: If the associated customer account is inactive.
    """
    customer = find_order_customer(customer_data.email, customer_data.phone)
    if customer and not customer.active:
        raise ValueError("La cuenta asociada a estos datos está desactivada.")
    if customer:
        return _update_order_customer(customer, customer_data)
    return _create_order_customer(customer_data)
