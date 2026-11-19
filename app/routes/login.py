from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from app.constants import HTTP_BAD_REQUEST, HTTP_OK
from app.services.auth_service import authenticate_customer, validate_login

LOGIN_BP = Blueprint("login", __name__)


def _render_login_form(form_data, status_code=HTTP_OK):
    """Render the login form with submitted data.

    Args:
        form_data (Mapping[str, str]): Values to refill the form.
        status_code (int): HTTP status code.

    Returns:
        tuple: Rendered response and status code.
    """
    return (
        render_template(
            "authentication/form.html",
            form_data=form_data,
            form_mode="login",
        ),
        status_code,
    )


@LOGIN_BP.route("/login", methods=["GET", "POST"])
def login():
    """Log in with email and password.

    Returns:
        Response | tuple: Redirect to home when credentials are valid;
        otherwise the login page with status 400.
    """
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        error = validate_login(email, password)
        if error:
            flash(error, "error")
            return _render_login_form(request.form, status_code=HTTP_BAD_REQUEST)

        customer = authenticate_customer(email, password)
        if not customer:
            flash("Correo o contraseña incorrectos.", "error")
            return _render_login_form(request.form, status_code=HTTP_BAD_REQUEST)

        session["customer_id"] = customer.id
        session["customer_name"] = customer.name
        flash(f"¡Hola de nuevo, {customer.name}! Sesión iniciada.", "ok")
        return redirect(url_for("home.index"))

    return _render_login_form({})


@LOGIN_BP.route("/logout")
def logout():
    """Log out the customer.

    Returns:
        Response: Redirect to the home page.
    """
    session.clear()
    flash("Sesión cerrada correctamente.", "ok")
    return redirect(url_for("home.index"))
