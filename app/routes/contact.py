from flask import Blueprint, current_app, render_template, request

from app.constants import (
    HTTP_BAD_REQUEST,
    HTTP_INTERNAL_SERVER_ERROR,
    HTTP_OK,
    HTTP_SERVICE_UNAVAILABLE,
)
from app.database import DatabaseUnavailableError, DatabaseWriteError
from app.services.contact_service import (
    normalize_contact_form,
    save_contact_message,
    validate_contact,
)

CONTACT_BP = Blueprint("contact", __name__)


def _render_contact_form(error=None, sent=False, sender_name="", status_code=HTTP_OK):
    """Render the contact form with an optional result message.

    Args:
        error (str | None): Validation or persistence error.
        sent (bool): Whether the message was saved successfully.
        sender_name (str): Name to show in the success message.
        status_code (int): HTTP status code.

    Returns:
        tuple: Rendered response and status code.
    """
    return (
        render_template(
            "contact/index.html",
            error=error,
            sent=sent,
            sender_name=sender_name,
        ),
        status_code,
    )


def _save_contact(fields, sender_name):
    """Store a validated contact message, returning an error response if needed.

    Args:
        fields (dict[str, str]): Validated contact fields.
        sender_name (str): Name used to refill the form on errors.

    Returns:
        tuple | None: Error response, or ``None`` when the message is saved.
    """
    try:
        save_contact_message(fields)
    except DatabaseUnavailableError:
        current_app.logger.exception("Database unavailable while saving contact")
        return _render_contact_form(
            error="No hay conexión con la base de datos. Inténtalo de nuevo en unos minutos.",
            sender_name=sender_name,
            status_code=HTTP_SERVICE_UNAVAILABLE,
        )
    except DatabaseWriteError:
        current_app.logger.exception("Could not save the contact message")
        return _render_contact_form(
            error="No pudimos guardar tu mensaje por un error interno. Inténtalo de nuevo.",
            sender_name=sender_name,
            status_code=HTTP_INTERNAL_SERVER_ERROR,
        )
    return None


def _handle_contact_submission():
    """Validate and store a submitted contact message.

    Returns:
        tuple: Rendered response and status code.
    """
    fields = normalize_contact_form(request.form)
    sender_name = fields["sender_name"]

    error = validate_contact(fields)
    if error:
        return _render_contact_form(
            error=error,
            sender_name=sender_name,
            status_code=HTTP_BAD_REQUEST,
        )

    error_response = _save_contact(fields, sender_name)
    if error_response:
        return error_response
    return _render_contact_form(sent=True, sender_name=sender_name)


@CONTACT_BP.route("/contacto", methods=["GET", "POST"])
def contact():
    """Show the contact module index or process a submitted message.

    Returns:
        Response | tuple: Index page or the contact form result.
    """
    if request.method == "POST":
        return _handle_contact_submission()
    return render_template(
        "contact/index.html",
        error=None,
        sent=False,
        sender_name="",
    )


@CONTACT_BP.route("/contacto/formulario", methods=["GET", "POST"])
def contact_form():
    """Show and process the contact form.

    Returns:
        tuple: Rendered contact form and HTTP status code.
    """
    if request.method == "POST":
        return _handle_contact_submission()
    return _render_contact_form()
