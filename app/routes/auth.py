from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from app.constants import (
    HTTP_BAD_REQUEST,
    HTTP_INTERNAL_SERVER_ERROR,
    HTTP_OK,
    HTTP_SERVICE_UNAVAILABLE,
)
from app.database import DatabaseUnavailableError, DatabaseWriteError
from app.services.auth_service import (
    DuplicateEmailError,
    find_registration_conflict,
    get_customer,
    normalize_profile_form,
    normalize_registration_form,
    register_customer,
    update_customer_profile,
    validate_profile,
    validate_registration,
)

AUTH_BP = Blueprint("auth", __name__)


def _render_account_form(form_data, form_mode, status_code=HTTP_OK):
    """Render an authentication form with submitted data.

    Args:
        form_data (Mapping[str, str]): Values to refill the form.
        form_mode (str): One of ``register``, ``login`` or ``edit``.
        status_code (int): HTTP status code.

    Returns:
        tuple: Rendered response and status code.
    """
    return (
        render_template(
            "authentication/form.html",
            form_data=form_data,
            form_mode=form_mode,
        ),
        status_code,
    )


def _render_registration_form(form_data, status_code=HTTP_OK):
    """Render the registration form with submitted data.

    Args:
        form_data (Mapping[str, str]): Values to refill the form.
        status_code (int): HTTP status code.

    Returns:
        tuple: Rendered response and status code.
    """
    return _render_account_form(form_data, "register", status_code)


@AUTH_BP.get("/cuenta")
def account():
    """Show the authentication module index.

    Returns:
        str: HTML of the authentication index page.
    """
    return render_template("authentication/index.html")


def _registration_failure(error, form_data):
    """Render the registration form for a persistence failure.

    Args:
        error (Exception): Raised persistence error.
        form_data (Mapping[str, str]): Values to refill the form.

    Returns:
        tuple: Rendered response and status code.
    """
    if isinstance(error, DuplicateEmailError):
        flash("Ya existe una cuenta con ese correo.", "error")
        return _render_registration_form(form_data, status_code=HTTP_BAD_REQUEST)
    if isinstance(error, DatabaseUnavailableError):
        current_app.logger.exception("Database unavailable while creating account")
        flash("No hay conexión con la base de datos. Inténtalo de nuevo en unos minutos.", "error")
        return _render_registration_form(form_data, status_code=HTTP_SERVICE_UNAVAILABLE)
    current_app.logger.exception("Error creating the account")
    flash("No pudimos guardar tu cuenta por un error interno. Inténtalo de nuevo.", "error")
    return _render_registration_form(form_data, status_code=HTTP_INTERNAL_SERVER_ERROR)


def _save_registration(fields, existing, form_data):
    """Register a validated account, returning an error response if needed.

    Args:
        fields (dict[str, str]): Validated registration fields.
        existing (Customer | None): Previous customer without a password.
        form_data (Mapping[str, str]): Values to refill the form.

    Returns:
        tuple | None: Error response, or ``None`` when the account is saved.
    """
    try:
        register_customer(fields, existing)
    except (DuplicateEmailError, DatabaseUnavailableError, DatabaseWriteError) as error:
        return _registration_failure(error, form_data)
    return None


def _handle_registration_post():
    """Validate and store a registration submission.

    Returns:
        Response | tuple: Redirect when the account is created; otherwise the
        registration page with the corresponding status code.
    """
    form_data = request.form
    fields = normalize_registration_form(form_data)
    errors = validate_registration(fields)
    existing = None
    if not errors:
        existing, errors = find_registration_conflict(fields["email"])

    if errors:
        for error in errors:
            flash(error, "error")
        return _render_registration_form(form_data, status_code=HTTP_BAD_REQUEST)

    error_response = _save_registration(fields, existing, form_data)
    if error_response:
        return error_response

    flash("¡Cuenta creada! Ahora inicia sesión para continuar.", "ok")
    return redirect(url_for("login.login"))


@AUTH_BP.route("/registro", methods=["GET", "POST"])
def register():
    """Register a new customer account or activate an existing one.

    Returns:
        Response | tuple: Redirect to login when the account is created;
        otherwise the registration page with 400 (invalid or duplicate data),
        503 (database unavailable) or 500 (save error).
    """
    if request.method == "POST":
        return _handle_registration_post()
    return _render_registration_form({})


def _profile_failure(error, form_data):
    """Render the profile form for a persistence failure.

    Args:
        error (Exception): Raised persistence error.
        form_data (Mapping[str, str]): Values to refill the form.

    Returns:
        tuple: Rendered response and status code.
    """
    if isinstance(error, DuplicateEmailError):
        flash("Ya existe una cuenta con ese correo.", "error")
        return _render_account_form(form_data, "edit", status_code=HTTP_BAD_REQUEST)
    if isinstance(error, DatabaseUnavailableError):
        current_app.logger.exception("Database unavailable while updating account")
        flash("No hay conexión con la base de datos. Inténtalo de nuevo en unos minutos.", "error")
        return _render_account_form(form_data, "edit", status_code=HTTP_SERVICE_UNAVAILABLE)
    current_app.logger.exception("Error updating the account")
    flash("No pudimos actualizar tu cuenta por un error interno. Inténtalo de nuevo.", "error")
    return _render_account_form(form_data, "edit", status_code=HTTP_INTERNAL_SERVER_ERROR)


def _save_profile_update(customer, fields, form_data):
    """Update a validated profile, returning an error response if needed.

    Args:
        customer (Customer): Signed-in customer being edited.
        fields (dict[str, str]): Validated profile fields.
        form_data (Mapping[str, str]): Values to refill the form.

    Returns:
        tuple[Customer | None, tuple | None]: Updated customer or an error
        response when saving fails.
    """
    try:
        return update_customer_profile(customer.id, fields), None
    except (DuplicateEmailError, DatabaseUnavailableError, DatabaseWriteError) as error:
        return None, _profile_failure(error, form_data)


def _handle_profile_update(customer):
    """Validate and save an account profile update.

    Args:
        customer (Customer): Signed-in customer being edited.

    Returns:
        Response | tuple: Redirect on success or the edit form with errors.
    """
    form_data = request.form
    fields = normalize_profile_form(form_data)
    errors = validate_profile(fields)
    if errors:
        for error in errors:
            flash(error, "error")
        return _render_account_form(form_data, "edit", status_code=HTTP_BAD_REQUEST)

    updated_customer, error_response = _save_profile_update(
        customer, fields, form_data
    )
    if error_response:
        return error_response

    session["customer_name"] = updated_customer.name
    flash("Tus datos se actualizaron correctamente.", "ok")
    return redirect(url_for("auth.edit_account"))


@AUTH_BP.route("/cuenta/editar", methods=["GET", "POST"])
def edit_account():
    """Show and process the profile form of the signed-in customer.

    Returns:
        Response | tuple: Login redirect when there is no session, the edit
        form on GET or validation errors, or a redirect after a successful
        update.
    """
    customer_id = session.get("customer_id")
    if not customer_id:
        flash("Inicia sesión para editar tu cuenta.", "error")
        return redirect(url_for("login.login"))

    customer = get_customer(customer_id)
    if not customer:
        session.clear()
        flash("La cuenta ya no existe. Inicia sesión de nuevo.", "error")
        return redirect(url_for("login.login"))

    if request.method == "POST":
        return _handle_profile_update(customer)

    form_data = {
        "name": customer.name,
        "email": customer.email or "",
        "phone": customer.phone or "",
    }
    return _render_account_form(form_data, "edit")
