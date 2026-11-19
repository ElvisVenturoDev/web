from flask import (
    Blueprint,
    abort,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from sqlalchemy.exc import IntegrityError

from app.constants import (
    HTTP_BAD_REQUEST,
    HTTP_INTERNAL_SERVER_ERROR,
    HTTP_NOT_FOUND,
    HTTP_OK,
    HTTP_SERVICE_UNAVAILABLE,
)
from app.database import DatabaseUnavailableError, DatabaseWriteError
from app.services.product_service import (
    get_product,
    load_products,
    normalize_product_form,
    product_form_values,
    save_product,
    validate_product,
)

PRODUCTS_BP = Blueprint("products", __name__)

PRODUCT_CATEGORIES = ("clasica", "superior", "suite", "familiar", "deluxe")


def _render_product_form(
    product, form_data, status_code=HTTP_OK, product_id=None
):
    """Render the shared product form for creation and edition.

    Args:
        product (Product | None): Product being edited, or ``None`` to create.
        form_data (Mapping[str, str]): Values to refill the form.
        status_code (int): HTTP status code.
        product_id (int | None): Product identifier for the form action.

    Returns:
        tuple: Rendered response and status code.
    """
    return (
        render_template(
            "products/form.html",
            product=product,
            product_id=product_id,
            form_data=form_data,
            categories=PRODUCT_CATEGORIES,
        ),
        status_code,
    )


def _product_save_error(error, product_id=None):
    """Render the product form for a persistence error.

    Args:
        error (Exception): Raised persistence error.
        product_id (int | None): Product being edited, or ``None`` to create.

    Returns:
        tuple: Rendered response and status code.
    """
    if isinstance(error, DatabaseUnavailableError):
        flash(
            "No hay conexión con la base de datos. Inténtalo de nuevo en unos minutos.",
            "error",
        )
        return _render_product_form(
            None, request.form, status_code=HTTP_SERVICE_UNAVAILABLE, product_id=product_id
        )
    flash(
        "No pudimos guardar el producto por un error interno. Inténtalo de nuevo.",
        "error",
    )
    return _render_product_form(
        None, request.form, status_code=HTTP_INTERNAL_SERVER_ERROR, product_id=product_id
    )


def _render_invalid_product_form(product_id):
    """Render the product form after a validation or duplicate-name error.

    Args:
        product_id (int | None): Product being edited, or ``None`` to create.

    Returns:
        tuple: Rendered response with status 400.
    """
    product = get_product(product_id) if product_id is not None else None
    return _render_product_form(
        product,
        request.form,
        status_code=HTTP_BAD_REQUEST,
        product_id=product_id,
    )


def _handle_product_save(product_id=None):
    """Validate and save a product submitted from the form.

    Args:
        product_id (int | None): Product being edited, or ``None`` to create.

    Returns:
        Response | tuple: Redirect on success or the form with errors.
    """
    fields = normalize_product_form(request.form)
    errors = validate_product(fields)
    if errors:
        for error in errors:
            flash(error, "error")
        return _render_invalid_product_form(product_id)

    try:
        save_product(fields, product_id)
    except IntegrityError:
        flash("Ya existe un producto con ese nombre. Usa otro nombre.", "error")
        return _render_invalid_product_form(product_id)
    except (DatabaseUnavailableError, DatabaseWriteError) as error:
        return _product_save_error(error, product_id)

    flash("Producto guardado correctamente.", "ok")
    return redirect(url_for("products.products"))


@PRODUCTS_BP.get("/habitaciones")
def products():
    """Show the product catalog.

    Returns:
        str: HTML of the products page.
    """
    return render_template("products/index.html", products=load_products())


@PRODUCTS_BP.route("/habitaciones/nueva", methods=["GET", "POST"])
def product_new():
    """Show and process the product creation form.

    Returns:
        Response | tuple: Form page on GET or validation errors; redirect to
        the catalog after saving.
    """
    if request.method == "POST":
        return _handle_product_save()
    return _render_product_form(None, {"active": "on"})


@PRODUCTS_BP.route("/habitaciones/<int:product_id>/editar", methods=["GET", "POST"])
def product_edit(product_id):
    """Show and process the product edition form.

    Args:
        product_id (int): Identifier of the product to edit.

    Returns:
        Response | tuple: Form page with the stored values, validation errors,
        or a redirect to the catalog after saving.
    """
    product = get_product(product_id)
    if product is None:
        abort(HTTP_NOT_FOUND)
    if request.method == "POST":
        return _handle_product_save(product_id)
    return _render_product_form(
        product,
        product_form_values(product),
        product_id=product.id,
    )
