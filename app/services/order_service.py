"""Order service: form validation and sale registration."""

import json
import re

from sqlalchemy.exc import IntegrityError

from app.constants import (
    ADDRESS_MAX_LENGTH,
    COMMENTS_MAX_LENGTH,
    DELIVERY_ADDRESS_NONE,
    DELIVERY_ADDRESS_PICKUP,
    DELIVERY_HOME,
    DELIVERY_PICKUP,
    DISTRICT_MAX_LENGTH,
    EMAIL_MAX_LENGTH,
    MIN_ORDER_QUANTITY,
    NAME_MAX_LENGTH,
    NAME_MIN_LENGTH,
    PHONE_PATTERN,
    VALID_DELIVERY_TYPES,
)
from app.database import transaction
from app.services.customer_service import (
    OrderCustomerData,
    get_or_create_order_customer,
)
from app.services.inventory_service import discount_stock
from app.services.product_service import (
    find_or_create_product,
    get_valid_product_names,
)
from app.services.sale_service import add_sale_detail, create_sale

NAME_PATTERN = re.compile(
    rf"[A-Za-zÁÉÍÓÚáéíóúÑñÜü' ]{{{NAME_MIN_LENGTH},{NAME_MAX_LENGTH}}}"
)
PHONE_RE = re.compile(PHONE_PATTERN)
EMAIL_PATTERN = re.compile(
    r"[a-z0-9._+\-]+@(gmail\.com|gmail\.com\.pe|hotmail\.com|outlook\.com|yahoo\.com|vallegrande\.edu\.pe)"
)


def _normalize_order_fields(form_data):
    """Normalize the order form values used by validation and saving.

    Args:
        form_data (Mapping[str, str]): Submitted form values.

    Returns:
        dict[str, str]: Normalized order fields.
    """
    return {
        "name": " ".join(form_data.get("name", "").split()),
        "phone": form_data.get("phone", "").strip(),
        "email": form_data.get("email", "").strip().lower(),
        "product": form_data.get("product", ""),
        "quantity": form_data.get("quantity", ""),
        "cart_products": form_data.get("cart_products", ""),
        "delivery_type": form_data.get("delivery") or DELIVERY_HOME,
        "address": form_data.get("address", "").strip(),
        "district": form_data.get("district", "").strip(),
        "comments": form_data.get("comments", "").strip(),
    }


def _validate_name(name):
    """Validate the customer name.

    Args:
        name (str): Normalized customer name.

    Returns:
        list[str]: Validation errors.
    """
    errors = []
    if not NAME_PATTERN.fullmatch(name) or len(name.replace(" ", "")) < NAME_MIN_LENGTH:
        errors.append("El nombre debe tener al menos 3 letras (solo letras y espacios).")
    if len(name) > NAME_MAX_LENGTH:
        errors.append(f"El nombre no puede superar {NAME_MAX_LENGTH} caracteres.")
    return errors


def _validate_phone(phone):
    """Validate the customer phone number.

    Args:
        phone (str): Submitted phone number.

    Returns:
        list[str]: Validation errors.
    """
    if not PHONE_RE.fullmatch(phone):
        return ["El teléfono debe tener 9 dígitos y empezar con 9."]
    return []


def _validate_email(email):
    """Validate the optional customer email.

    Args:
        email (str): Normalized email address.

    Returns:
        list[str]: Validation errors.
    """
    if len(email) > EMAIL_MAX_LENGTH:
        return [f"El correo no puede superar {EMAIL_MAX_LENGTH} caracteres."]
    if email and not EMAIL_PATTERN.fullmatch(email):
        return ["El correo debe estar en minúsculas y usar un dominio permitido (ej. @gmail.com)."]
    return []


def _valid_product_names(products):
    """Get valid product names from loaded products or the catalog.

    Args:
        products (list[dict] | None): Already loaded products.

    Returns:
        set[str]: Valid product names.
    """
    if products is not None:
        return {product["name"] for product in products}
    return get_valid_product_names()


def _validate_cart_item(cart_item, valid_names):
    """Validate one product entry from the cart.

    Args:
        cart_item (Any): Cart entry to validate.
        valid_names (set[str]): Valid product names.

    Returns:
        list[str]: Validation errors.
    """
    if not isinstance(cart_item, dict) or not isinstance(cart_item.get("name"), str):
        return ["Hay un producto con formato inválido en el carrito."]

    errors = []
    if cart_item.get("name") not in valid_names:
        errors.append(f"Producto no válido: {cart_item.get('name', 'desconocido')}.")
    if (
        not isinstance(cart_item.get("quantity"), int)
        or cart_item.get("quantity", 0) < MIN_ORDER_QUANTITY
    ):
        errors.append(
            "Las cantidades deben ser números enteros de "
            f"{MIN_ORDER_QUANTITY} o más."
        )
    return errors


def _parse_cart_items(cart_products):
    """Parse the serialized cart into a list of product entries.

    Args:
        cart_products (str): JSON-encoded cart items.

    Returns:
        tuple[list | None, list[str]]: Parsed items and validation errors.
        Items are ``None`` when the cart cannot be parsed or is empty.
    """
    try:
        cart_items = json.loads(cart_products)
    except (json.JSONDecodeError, TypeError):
        return None, ["Error al procesar los productos del carrito."]

    if not isinstance(cart_items, list) or len(cart_items) == 0:
        return None, ["El carrito está vacío."]
    return cart_items, []


def _validate_cart_items(cart_products, valid_names):
    """Validate a serialized cart with one or more products.

    Args:
        cart_products (str): JSON-encoded cart items.
        valid_names (set[str]): Valid product names.

    Returns:
        list[str]: Validation errors.
    """
    cart_items, errors = _parse_cart_items(cart_products)
    if errors:
        return errors

    for cart_item in cart_items:
        errors.extend(_validate_cart_item(cart_item, valid_names))
    return errors


def _validate_single_product(form_data, valid_names):
    """Validate the single-product order fields.

    Args:
        form_data (Mapping[str, str]): Submitted form values.
        valid_names (set[str]): Valid product names.

    Returns:
        list[str]: Validation errors.
    """
    errors = []
    if form_data.get("product", "") not in valid_names:
        errors.append("Selecciona un producto válido.")
    try:
        if int(form_data.get("quantity", "")) < MIN_ORDER_QUANTITY:
            raise ValueError
    except (TypeError, ValueError):
        errors.append(
            "La cantidad debe ser un número entero de "
            f"{MIN_ORDER_QUANTITY} o más."
        )
    return errors


def _validate_products(form_data, products):
    """Validate the ordered products, either from the cart or a single item.

    Args:
        form_data (Mapping[str, str]): Submitted form values.
        products (list[dict] | None): Already loaded products.

    Returns:
        list[str]: Validation errors.
    """
    valid_names = _valid_product_names(products)
    cart_products = form_data.get("cart_products", "")
    if cart_products:
        return _validate_cart_items(cart_products, valid_names)
    return _validate_single_product(form_data, valid_names)


def _validate_delivery(fields):
    """Validate the delivery type, address and district.

    Args:
        fields (dict[str, str]): Normalized order fields.

    Returns:
        list[str]: Validation errors.
    """
    errors = []
    if fields["delivery_type"] not in VALID_DELIVERY_TYPES:
        errors.append("Selecciona una modalidad de entrega.")
    if len(fields["address"]) > ADDRESS_MAX_LENGTH:
        errors.append(f"La dirección de entrega no puede superar {ADDRESS_MAX_LENGTH} caracteres.")
    if len(fields["district"]) > DISTRICT_MAX_LENGTH:
        errors.append(f"El distrito no puede superar {DISTRICT_MAX_LENGTH} caracteres.")
    if fields["delivery_type"] == DELIVERY_HOME:
        if not fields["address"]:
            errors.append("Ingresa la dirección de entrega.")
        if not fields["district"]:
            errors.append("Ingresa el distrito o localidad.")
    return errors


def _validate_comments(form_data, fields):
    """Validate comments and terms acceptance.

    Args:
        form_data (Mapping[str, str]): Submitted form values.
        fields (dict[str, str]): Normalized order fields.

    Returns:
        list[str]: Validation errors.
    """
    errors = []
    if len(fields["comments"]) > COMMENTS_MAX_LENGTH:
        errors.append(f"Los comentarios no pueden superar {COMMENTS_MAX_LENGTH} caracteres.")
    if "confirmation" in form_data and not form_data.get("confirmation"):
        errors.append("Debes aceptar los términos para enviar el pedido.")
    return errors


def validate_order(form_data, products=None):
    """Validate the data submitted by the order form.

    Args:
        form_data (Mapping[str, str]): Submitted form values.
        products (list[dict] | None): Already loaded products. When ``None``
            they are obtained with ``load_products()``.

    Returns:
        list[str]: Validation errors. An empty list means the order is valid.
    """
    fields = _normalize_order_fields(form_data)
    errors = []
    errors.extend(_validate_name(fields["name"]))
    errors.extend(_validate_phone(fields["phone"]))
    errors.extend(_validate_email(fields["email"]))
    errors.extend(_validate_products(form_data, products))
    errors.extend(_validate_delivery(fields))
    errors.extend(_validate_comments(form_data, fields))
    return errors


def _order_items(form_data):
    """Extract ordered products from the cart or the single product field.

    Args:
        form_data (Mapping[str, str]): Validated form values.

    Returns:
        list[tuple[str, int]]: Pairs of ``(product_name, quantity)``.
    """
    cart_products = form_data.get("cart_products", "")
    if cart_products:
        return [
            (cart_item["name"], int(cart_item["quantity"]))
            for cart_item in json.loads(cart_products)
        ]
    return [(form_data["product"], int(form_data["quantity"]))]


def _delivery_values(delivery_type, address, district):
    """Build the delivery and customer-detail address values.

    Args:
        delivery_type (str): Selected delivery type.
        address (str | None): Submitted address.
        district (str | None): Submitted district.

    Returns:
        tuple[str, str | None, str, str | None]: Sale address, sale district,
        customer-detail address and customer-detail district.
    """
    if delivery_type == DELIVERY_PICKUP:
        return (
            DELIVERY_ADDRESS_PICKUP,
            None,
            DELIVERY_ADDRESS_NONE,
            None,
        )
    delivery_address = address or DELIVERY_ADDRESS_NONE
    return delivery_address, district, delivery_address, district


def _add_sale_items(sale_id, order_items):
    """Persist the product lines of a sale.

    Args:
        sale_id (int): Sale identifier.
        order_items (list[tuple[str, int]]): Product names and quantities.
    """
    for product_name, quantity in order_items:
        product = find_or_create_product(product_name)
        discount_stock(product.id, quantity)
        add_sale_detail(sale_id, product, quantity)


def _customer_data(fields, delivery_values):
    """Build the customer data required to register the order.

    Args:
        fields (dict[str, str]): Normalized order fields.
        delivery_values (tuple): Values returned by ``_delivery_values``.

    Returns:
        OrderCustomerData: Customer values from the order.
    """
    _, _, detail_address, detail_district = delivery_values
    return OrderCustomerData(
        name=fields["name"],
        phone=fields["phone"],
        email=fields["email"] or None,
        detail_address=detail_address,
        detail_district=detail_district,
        update_address=fields["delivery_type"] == DELIVERY_HOME,
    )


def _persist_order(fields, delivery_values):
    """Persist the customer, sale and sale details in one transaction.

    Args:
        fields (dict[str, str]): Normalized order fields.
        delivery_values (tuple): Values returned by ``_delivery_values``.

    Returns:
        int: Identifier of the created sale.
    """
    delivery_address, delivery_district, _, _ = delivery_values
    with transaction():
        customer = get_or_create_order_customer(
            _customer_data(fields, delivery_values)
        )
        sale = create_sale(
            customer.id,
            fields["delivery_type"],
            delivery_address,
            delivery_district,
            fields["comments"] or None,
        )
        _add_sale_items(sale.id, _order_items(fields))
        return sale.id


def _saved_order_fields(form_data):
    """Normalize and trim the values stored for an order.

    Args:
        form_data (Mapping[str, str]): Form values validated with
            ``validate_order``.

    Returns:
        dict[str, str]: Normalized and trimmed order fields.
    """
    fields = _normalize_order_fields(form_data)
    fields["address"] = fields["address"][:ADDRESS_MAX_LENGTH] or None
    fields["district"] = fields["district"][:DISTRICT_MAX_LENGTH] or None
    fields["comments"] = fields["comments"][:COMMENTS_MAX_LENGTH] or None
    return fields


def save_order(form_data):
    """Register an order in a single transaction.

    Args:
        form_data (Mapping[str, str]): Form values validated with
            ``validate_order``.

    Returns:
        int: Identifier of the created sale.

    Raises:
        ValueError: If the customer is inactive or a product is unavailable.
        DatabaseUnavailableError: If the database is unavailable.
        DatabaseWriteError: If the database cannot save the order.
    """
    fields = _saved_order_fields(form_data)
    delivery_values = _delivery_values(
        fields["delivery_type"],
        fields["address"],
        fields["district"],
    )

    try:
        return _persist_order(fields, delivery_values)
    except IntegrityError as error:
        raise ValueError(
            "No pudimos registrar el pedido porque ya existe un registro con "
            "esos datos. Inténtalo de nuevo."
        ) from error
