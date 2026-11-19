"""Contact service: validation and storage of contact messages."""

import re

from flask import request

from app.constants import (
    CONTACT_MESSAGE_MAX_LENGTH,
    CONTACT_MOBILE_PATTERN,
    CONTACT_NAME_MAX_LENGTH,
    CONTACT_SUBJECT_MAX_LENGTH,
    CONTACT_USER_AGENT_MAX_LENGTH,
    EMAIL_MAX_LENGTH,
    IP_MAX_LENGTH,
)
from app.database import transaction
from app.models import ContactMessage

email_pattern = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")
mobile_pattern = re.compile(CONTACT_MOBILE_PATTERN)


def normalize_contact_form(form_data):
    """Clean the fields of the contact form.

    Args:
        form_data (Mapping[str, str]): Submitted form values.

    Returns:
        dict[str, str]: Normalized ``sender_name``, ``mobile``, ``email``,
        ``subject`` and ``message`` values.
    """
    return {
        "sender_name": " ".join(form_data.get("name", "").split()),
        "mobile": re.sub(r"[\s().-]+", "", form_data.get("mobile", "")),
        "email": form_data.get("email", "").strip().lower(),
        "subject": form_data.get("subject", "").strip(),
        "message": form_data.get("message", "").strip(),
    }


def _validate_contact_identity(sender_name, mobile, message):
    """Validate the required contact identity fields.

    Args:
        sender_name (str): Normalized sender name.
        mobile (str): Normalized mobile number.
        message (str): Message body.

    Returns:
        str | None: First validation error, or ``None`` when valid.
    """
    if not sender_name or not mobile or not message:
        return "Completa tu nombre, celular y mensaje."
    if len(sender_name) > CONTACT_NAME_MAX_LENGTH:
        return f"El nombre no puede superar {CONTACT_NAME_MAX_LENGTH} caracteres."
    if not mobile_pattern.fullmatch(mobile):
        return "Ingresa un celular válido (solo números, máximo 15 caracteres)."
    return None


def _validate_contact_details(fields):
    """Validate the optional contact fields and message limits.

    Args:
        fields (dict[str, str]): Normalized contact fields.

    Returns:
        str | None: First validation error, or ``None`` when valid.
    """
    email = fields["email"]
    if email and (len(email) > EMAIL_MAX_LENGTH or not email_pattern.fullmatch(email)):
        return "Ingresa un correo válido."
    if len(fields["subject"]) > CONTACT_SUBJECT_MAX_LENGTH:
        return f"El asunto no puede superar {CONTACT_SUBJECT_MAX_LENGTH} caracteres."
    if len(fields["message"]) > CONTACT_MESSAGE_MAX_LENGTH:
        return f"El mensaje es demasiado largo (máximo {CONTACT_MESSAGE_MAX_LENGTH} caracteres)."
    return None


def validate_contact(fields):
    """Validate the fields of a contact message.

    Args:
        fields (dict[str, str]): Result of ``normalize_contact_form``.

    Returns:
        str | None: First validation error, or ``None`` when the message is
        valid.
    """
    identity_error = _validate_contact_identity(
        fields["sender_name"],
        fields["mobile"],
        fields["message"],
    )
    if identity_error:
        return identity_error
    return _validate_contact_details(fields)


def _request_metadata():
    """Read the visitor metadata needed by a contact message.

    Returns:
        tuple[str, str]: Visitor IP address and ``User-Agent`` header.
    """
    forwarded = request.headers.get("X-Forwarded-For", "")
    ip_address = (
        forwarded.split(",")[0].strip() or request.remote_addr or ""
    )[:IP_MAX_LENGTH]
    return ip_address, request.headers.get("User-Agent", "")


def save_contact_message(fields):
    """Store a contact message with its request metadata.

    Args:
        fields (dict[str, str]): Validated contact fields.

    Returns:
        None: The message is stored in the current transaction.

    Raises:
        DatabaseUnavailableError: If the database is unavailable.
        DatabaseWriteError: If the database cannot save the message.
    """
    ip_address, user_agent = _request_metadata()
    contact_message = ContactMessage(
        name=fields["sender_name"],
        mobile=fields["mobile"],
        email=fields["email"] or None,
        subject=fields["subject"] or None,
        message=fields["message"],
        ip=ip_address or None,
        user_agent=user_agent[:CONTACT_USER_AGENT_MAX_LENGTH] or None,
    )
    with transaction() as session:
        session.add(contact_message)
