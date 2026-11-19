"""Administrator authentication and session helpers."""

from datetime import datetime

from flask import current_app, session

from app.database import db, transaction
from app.models import AdminUser
from app.services.audit_service import log_action
from app.timeutil import now_lima


def authenticate(email, password):
    """Return the active user when the credentials are valid."""
    email = (email or "").strip().lower()
    user = db.session.scalars(
        db.select(AdminUser).filter(db.func.lower(AdminUser.email) == email).limit(1)
    ).first()
    if user is None or not user.active or not user.check_password(password or ""):
        return None
    return user


def start_session(user):
    """Persist the authenticated user in the Flask session."""
    session.clear()
    session.permanent = True
    session["admin_user_id"] = int(user.id)
    session["admin_role"] = user.role
    session["admin_name"] = user.name
    session["last_activity"] = now_lima().isoformat()
    return user


def touch_session():
    """Refresh the inactivity marker."""
    session["last_activity"] = now_lima().isoformat()


def session_expired():
    """Whether the session exceeded the configured idle time."""
    raw = session.get("last_activity")
    if not raw:
        return True
    try:
        last = datetime.fromisoformat(raw)
    except ValueError:
        return True
    limit = current_app.config.get("ADMIN_IDLE_MINUTES", 30)
    return (now_lima() - last).total_seconds() > limit * 60


def current_user():
    """Return the logged in administrator or ``None``."""
    user_id = session.get("admin_user_id")
    if not user_id:
        return None
    return db.session.get(AdminUser, user_id)


def mark_login(user):
    """Update the last login timestamp."""
    with transaction() as session_db:
        stored = session_db.get(AdminUser, user.id)
        if stored is not None:
            stored.last_login_at = now_lima()
    log_action("auth.login", entity="admin_users", entity_id=user.id,
               admin_user_id=user.id, commit=True)


def register_failed_login(email):
    """Audit a failed login attempt without exposing the password."""
    log_action(
        "auth.login_failed",
        entity="admin_users",
        detail=f"Intento fallido para {email or 'correo vacío'}",
        commit=True,
    )


def register_logout(user_id):
    """Audit a logout."""
    log_action("auth.logout", entity="admin_users", entity_id=user_id, commit=True)
