"""Audit trail helpers."""

from flask import has_request_context, session

from app.database import db
from app.models import AuditLog


def log_action(
    action,
    entity=None,
    entity_id=None,
    detail=None,
    admin_user_id=None,
    commit=False,
):
    """Append an audit entry.

    Args:
        action: Short action key, e.g. ``reservation.create``.
        entity: Affected table/entity name.
        entity_id: Affected row identifier.
        detail: Human readable detail (never secrets).
        admin_user_id: Actor identifier; defaults to the session user.
        commit: Commit immediately (used for failed logins outside a request
            transaction).
    """
    if admin_user_id is None and has_request_context():
        admin_user_id = session.get("admin_user_id")
    entry = AuditLog(
        admin_user_id=admin_user_id,
        action=action,
        entity=entity,
        entity_id=entity_id,
        detail=detail,
    )
    db.session.add(entry)
    if commit:
        db.session.commit()
    return entry
