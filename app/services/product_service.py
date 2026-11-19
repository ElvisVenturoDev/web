"""Product service: catalog, prices, stock and product management."""

from flask import current_app
from sqlalchemy.exc import SQLAlchemyError

from app.catalog import PRODUCTS
from app.constants import (
    CATEGORY_FALLBACK,
    DEFAULT_MIN_STOCK,
    PRODUCT_CATEGORY_MAX_LENGTH,
    PRODUCT_DETAIL_MAX_LENGTH,
    PRODUCT_IMAGE_URL_MAX_LENGTH,
    PRODUCT_NAME_MAX_LENGTH,
    WEB_CATEGORIES,
)
from app.database import db, transaction
from app.images import local_image_url
from app.models import Inventory, Product


def _read_stored_products():
    """Read stored products from the database.

    Returns:
        list[Product]: Stored products ordered by identifier, or an empty list
        when the database is unavailable.
    """
    try:
        return db.session.scalars(
            db.select(Product).order_by(Product.id)
        ).all()
    except SQLAlchemyError:
        # The public catalog falls back to catalog.py when the database fails.
        current_app.logger.exception("Could not read the database")
        return []


def _stored_product_data(stored_product):
    """Convert a stored product into the dictionary used by catalog merging.

    Args:
        stored_product (Product): Product loaded from the database.

    Returns:
        dict: Product values with inventory data.
    """
    inventory = stored_product.inventory
    return {
        "id": stored_product.id,
        "name": stored_product.name,
        "category": stored_product.category,
        "detail": stored_product.detail,
        "description": stored_product.description,
        "price": stored_product.price,
        "image_url": stored_product.image_url,
        "active": stored_product.active,
        "stock": inventory.stock if inventory else 0,
        "min_stock": inventory.min_stock if inventory else DEFAULT_MIN_STOCK,
    }


def _load_database_rows():
    """Read the stored products as dictionaries for catalog merging.

    Returns:
        list[dict]: Product rows with their inventory data, or an empty list if
        the database is unavailable.
    """
    return [
        _stored_product_data(stored_product)
        for stored_product in _read_stored_products()
    ]


def _apply_stored_product(product, row):
    """Apply database values over a catalog product.

    Args:
        product (dict): Catalog product to enrich.
        row (dict): Stored product data.

    Returns:
        dict: The updated catalog product.
    """
    product["price"] = float(row["price"])
    product["stock"] = int(row["stock"] or 0)
    product["min_stock"] = int(row["min_stock"] or 0)
    product["sold_out"] = product["stock"] <= 0
    product["product_id"] = row["id"]
    if row["detail"]:
        product["detail"] = row["detail"]
    if row["description"]:
        product["description"] = row["description"]
    if row["image_url"]:
        product["image"] = local_image_url(row["image_url"], row["category"])
    return product


def _merge_catalog_products(products, rows):
    """Merge stored data into the visual catalog products.

    Args:
        products (list[dict]): Products from ``catalog.py``.
        rows (list[dict]): Stored products from the database.

    Returns:
        list[dict]: Visible catalog products updated with stored data.
    """
    rows_by_name = {(row["name"] or "").strip().casefold(): row for row in rows}
    visible_products = []
    for product in products:
        row = rows_by_name.get(product["name"].strip().casefold())
        if row and not row["active"]:
            continue

        if not row:
            product["stock"] = 0
            product["min_stock"] = 0
            product["sold_out"] = True
            product["product_id"] = None
            visible_products.append(product)
            continue

        visible_products.append(_apply_stored_product(product, row))

    return visible_products


def _database_product(row):
    """Build a visible product from a database-only row.

    Args:
        row (dict): Stored product data.

    Returns:
        dict: Product exposed by the website.
    """
    category = (row["category"] or "").lower()
    if category not in WEB_CATEGORIES:
        category = CATEGORY_FALLBACK
    stock = int(row["stock"] or 0)
    detail = (row["detail"] or row["description"] or "").strip()
    return {
        "id": f"db-{row['id']}",
        "product_id": row["id"],
        "name": row["name"],
        "detail": detail,
        "description": row["description"] or "",
        "category": category,
        "price": float(row["price"]),
        "featured": False,
        "rating": 0,
        "stock": stock,
        "min_stock": int(row["min_stock"] or 0),
        "sold_out": stock <= 0,
        "image": local_image_url(row["image_url"], category),
        "alt": row["name"],
    }


def _database_only_products(rows, catalog_names):
    """Build products that exist only in the database.

    Args:
        rows (list[dict]): Stored products from the database.
        catalog_names (set[str]): Normalized names present in ``catalog.py``.

    Returns:
        list[dict]: Additional visible products.
    """
    products = []
    for row in rows:
        if not row["active"]:
            continue
        if (row["name"] or "").strip().casefold() in catalog_names:
            continue
        products.append(_database_product(row))
    return products


def _catalog_products():
    """Copy the fallback catalog so callers cannot mutate the source.

    Returns:
        list[dict]: Independent catalog product dictionaries.
    """
    return [dict(catalog_product) for catalog_product in PRODUCTS]


def _catalog_names(products):
    """Build the normalized names present in the fallback catalog.

    Args:
        products (list[dict]): Catalog products.

    Returns:
        set[str]: Normalized product names.
    """
    return {product["name"].strip().casefold() for product in products}


def load_products():
    """Load the catalog with updated prices and stock.

    Returns:
        list[dict]: Visible products, including ``name``, ``price``, ``stock``,
        ``min_stock``, ``sold_out``, ``product_id`` and ``image``.
    """
    catalog_products = _catalog_products()
    stored_rows = _load_database_rows()
    visible_products = _merge_catalog_products(catalog_products, stored_rows)
    visible_products.extend(
        _database_only_products(stored_rows, _catalog_names(catalog_products))
    )
    return visible_products


def get_valid_product_names():
    """Get the product names that can be ordered.

    Returns:
        set[str]: Names from the catalog combined with the database.
    """
    return {product["name"] for product in load_products()}


def get_product(product_id):
    """Return a stored product by identifier.

    Args:
        product_id (int): Product identifier.

    Returns:
        Product | None: Found product or ``None``.
    """
    return db.session.get(Product, product_id)


def product_form_values(product):
    """Return the values used to prefill the product edit form.

    Args:
        product (Product): Product being edited.

    Returns:
        dict[str, str]: Form values for the product.
    """
    inventory = product.inventory
    return {
        "name": product.name,
        "category": product.category,
        "detail": product.detail or "",
        "description": product.description or "",
        "price": f"{float(product.price):.2f}",
        "image_url": product.image_url or "",
        "stock": str(inventory.stock if inventory else 0),
        "min_stock": str(
            inventory.min_stock if inventory else DEFAULT_MIN_STOCK
        ),
        "active": "on" if product.active else "",
    }


def normalize_product_form(form_data):
    """Clean the values of the product form.

    Args:
        form_data (Mapping[str, str]): Submitted form values.

    Returns:
        dict[str, str]: Normalized product fields.
    """
    return {
        "name": " ".join(form_data.get("name", "").split()),
        "category": (
            form_data.get("category", "").strip().lower() or CATEGORY_FALLBACK
        ),
        "detail": form_data.get("detail", "").strip(),
        "description": form_data.get("description", "").strip(),
        "price": form_data.get("price", "").strip(),
        "image_url": form_data.get("image_url", "").strip(),
        "stock": form_data.get("stock", "").strip(),
        "min_stock": form_data.get("min_stock", "").strip(),
        "active": bool(form_data.get("active")),
    }


def _validate_product_text(fields):
    """Validate the product text fields and their limits.

    Args:
        fields (dict[str, str]): Normalized product fields.

    Returns:
        list[str]: Validation errors.
    """
    errors = []
    if not fields["name"]:
        errors.append("Ingresa el nombre del producto.")
    elif len(fields["name"]) > PRODUCT_NAME_MAX_LENGTH:
        errors.append(
            f"El nombre no puede superar {PRODUCT_NAME_MAX_LENGTH} caracteres."
        )
    if len(fields["category"]) > PRODUCT_CATEGORY_MAX_LENGTH:
        errors.append(
            f"La categoría no puede superar {PRODUCT_CATEGORY_MAX_LENGTH} caracteres."
        )
    if len(fields["detail"]) > PRODUCT_DETAIL_MAX_LENGTH:
        errors.append(
            f"El detalle no puede superar {PRODUCT_DETAIL_MAX_LENGTH} caracteres."
        )
    if len(fields["image_url"]) > PRODUCT_IMAGE_URL_MAX_LENGTH:
        errors.append(
            "La URL de la imagen no puede superar "
            f"{PRODUCT_IMAGE_URL_MAX_LENGTH} caracteres."
        )
    return errors


def _validate_product_price(fields):
    """Validate the product price.

    Args:
        fields (dict[str, str]): Normalized product fields.

    Returns:
        list[str]: Validation errors.
    """
    try:
        price = float(fields["price"])
    except (TypeError, ValueError):
        return ["Ingresa un precio válido."]
    if price < 0:
        return ["El precio no puede ser negativo."]
    return []


def _validate_product_stock(fields):
    """Validate the stock and minimum stock values.

    Args:
        fields (dict[str, str]): Normalized product fields.

    Returns:
        list[str]: Validation errors.
    """
    errors = []
    for key, label in (("stock", "stock"), ("min_stock", "stock mínimo")):
        try:
            value = int(fields[key])
        except (TypeError, ValueError):
            errors.append(f"Ingresa un {label} válido.")
            continue
        if value < 0:
            errors.append(f"El {label} no puede ser negativo.")
    return errors


def validate_product(fields):
    """Validate the product form values.

    Args:
        fields (dict[str, str]): Result of ``normalize_product_form``.

    Returns:
        list[str]: Validation errors. An empty list means the data is valid.
    """
    errors = []
    errors.extend(_validate_product_text(fields))
    errors.extend(_validate_product_price(fields))
    errors.extend(_validate_product_stock(fields))
    return errors


def _apply_product_fields(product, fields):
    """Copy the validated values into a product row.

    Args:
        product (Product): Product to update.
        fields (dict[str, str]): Validated product fields.

    Returns:
        Product: Updated product.
    """
    product.name = fields["name"]
    product.category = fields["category"]
    product.detail = fields["detail"] or None
    product.description = fields["description"] or None
    product.price = float(fields["price"])
    product.image_url = fields["image_url"] or None
    product.active = fields["active"]
    return product


def _product_inventory(product):
    """Return the inventory row of a product, creating it when missing.

    Args:
        product (Product): Product whose inventory is needed.

    Returns:
        Inventory: Product inventory.
    """
    if product.inventory is None:
        product.inventory = Inventory(
            stock=0, min_stock=DEFAULT_MIN_STOCK
        )
    return product.inventory


def save_product(fields, product_id=None):
    """Create or update a product and its inventory.

    Args:
        fields (dict[str, str]): Validated product fields.
        product_id (int | None): Product to update; ``None`` creates a new one.

    Returns:
        Product: Saved product.

    Raises:
        ValueError: If the product to update does not exist.
        DatabaseUnavailableError: If the database is unavailable.
        DatabaseWriteError: If the database cannot save the product.
    """
    with transaction() as session:
        if product_id is None:
            product = Product()
            session.add(product)
        else:
            product = session.get(Product, product_id)
            if product is None:
                raise ValueError("El producto ya no existe.")

        _apply_product_fields(product, fields)
        session.flush()
        inventory = _product_inventory(product)
        inventory.stock = int(fields["stock"])
        inventory.min_stock = int(fields["min_stock"])
    return product


def _product_field(product, key, default=None):
    """Read a product value from a dictionary or object.

    Args:
        product (dict | object): Catalog product.
        key (str): Value name to read.
        default (Any): Value returned when the key is missing.

    Returns:
        Any: Product value or ``default``.
    """
    if isinstance(product, dict):
        return product.get(key, default)
    return getattr(product, key, default)


def _product_name(product):
    """Return a catalog product name.

    Args:
        product (dict | object): Catalog product.

    Returns:
        str: Product name or an empty string.
    """
    return _product_field(product, "name", "")


def _find_catalog_product(product_name):
    """Find a catalog definition by product name.

    Args:
        product_name (str): Requested product name.

    Returns:
        dict | None: Catalog definition or ``None`` when missing.
    """
    return next(
        (
            catalog_item
            for catalog_item in PRODUCTS
            if _product_name(catalog_item) == product_name
        ),
        None,
    )


def _catalog_product_values(catalog_product):
    """Build product column values from a catalog definition.

    Args:
        catalog_product (dict): Catalog product definition.

    Returns:
        dict: Values accepted by the ``Product`` model.
    """
    return {
        "name": _product_name(catalog_product),
        "category": (
            _product_field(catalog_product, "category", CATEGORY_FALLBACK)
            or CATEGORY_FALLBACK
        )[:PRODUCT_CATEGORY_MAX_LENGTH],
        "detail": (
            _product_field(catalog_product, "detail", "") or ""
        )[:PRODUCT_DETAIL_MAX_LENGTH] or None,
        "description": _product_field(catalog_product, "description", None),
        "price": _product_field(catalog_product, "price", 0),
        "image_url": _product_field(catalog_product, "image", None),
    }


def _create_product_from_catalog(product_name):
    """Create a database product from its ``catalog.py`` definition.

    Args:
        product_name (str): Requested product name.

    Returns:
        Product: New product added to the session.

    Raises:
        ValueError: If the product is not present in the catalog.
    """
    catalog_product = _find_catalog_product(product_name)
    if not catalog_product:
        raise ValueError(
            f"El producto «{product_name}» no está disponible en el catálogo."
        )

    product = Product(**_catalog_product_values(catalog_product))
    db.session.add(product)
    db.session.flush()
    return product


def find_or_create_product(product_name):
    """Get a product by name, creating it from ``catalog.py`` when missing.

    Args:
        product_name (str): Requested product name.

    Returns:
        Product: Product stored in the database.

    Raises:
        ValueError: If the product is inactive or missing from the catalog.
    """
    product = db.session.scalars(
        db.select(Product).filter_by(name=product_name).limit(1)
    ).first()
    if product:
        if not product.active:
            raise ValueError(f"El producto «{product_name}» no está disponible.")
        return product
    return _create_product_from_catalog(product_name)
