from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)

from app.constants import (
    HTTP_BAD_REQUEST,
    HTTP_INTERNAL_SERVER_ERROR,
    HTTP_OK,
    HTTP_SERVICE_UNAVAILABLE,
)
from app.database import DatabaseUnavailableError, DatabaseWriteError
from app.services.order_service import save_order, validate_order
from app.services.product_service import load_products

ORDER_FORM_BP = Blueprint("order_form", __name__)


def _render_order_form(products, form_data, selected_product="", status_code=HTTP_OK):
    """Render the order form with products and submitted data.

    Args:
        products (list[dict]): Products available for the order.
        form_data (Mapping[str, str]): Values to refill the form.
        selected_product (str): Product preselected in the form.
        status_code (int): HTTP status code.

    Returns:
        tuple: Rendered response and status code.
    """
    return (
        render_template(
            "orders/form.html",
            products=products,
            selected_product=selected_product,
            form_data=form_data,
        ),
        status_code,
    )


@ORDER_FORM_BP.get("/pedidos")
def orders_index():
    """Show the orders module index.

    Returns:
        str: HTML of the orders index page.
    """
    return render_template("orders/index.html")


def _try_save_order(form_data):
    """Save an order and translate persistence errors into form messages.

    Args:
        form_data (Mapping[str, str]): Validated form values.

    Returns:
        tuple[list[str], int]: Errors and HTTP status code.
    """
    try:
        save_order(form_data)
        return [], HTTP_OK
    except ValueError as error:
        return [str(error)], HTTP_BAD_REQUEST
    except DatabaseUnavailableError:
        current_app.logger.exception("Database unavailable while saving order")
        return [
            "No hay conexión con la base de datos. Inténtalo de nuevo en unos minutos."
        ], HTTP_SERVICE_UNAVAILABLE
    except DatabaseWriteError:
        current_app.logger.exception("Error saving the order")
        return [
            "No pudimos guardar tu pedido por un error interno. Inténtalo de nuevo."
        ], HTTP_INTERNAL_SERVER_ERROR


def _handle_order_submission(products):
    """Validate and save a submitted order.

    Args:
        products (list[dict]): Products available for the order.

    Returns:
        Response | tuple: Form page on errors or redirect on success.
    """
    errors = validate_order(request.form, products)
    status_code = HTTP_BAD_REQUEST
    if not errors:
        errors, status_code = _try_save_order(request.form)

    if errors:
        for error in errors:
            flash(error, "error")
        return _render_order_form(
            products,
            request.form,
            selected_product=request.form.get("product", ""),
            status_code=status_code,
        )

    flash(
        "¡Pedido recibido! Confirmaremos la disponibilidad y entrega por WhatsApp.",
        "ok",
    )
    return redirect(url_for("order_form.order_registered"))


@ORDER_FORM_BP.route("/formulario", methods=["GET", "POST"])
def order_form():
    """Show the order form and process its submission.

    Returns:
        Response: The form page (400 for invalid data, 503 when the database
        is unavailable, 500 when saving fails) or a redirect to the
        order-registered page.
    """
    products = load_products()
    if request.method == "POST":
        return _handle_order_submission(products)
    return _render_order_form(
        products,
        {},
        selected_product=request.args.get("product", ""),
    )


@ORDER_FORM_BP.get("/pedido-registrado")
def order_registered():
    """Show the order registration confirmation.

    Returns:
        str: HTML of the confirmation page.
    """
    return render_template("orders/order_registered.html")
