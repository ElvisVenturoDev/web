"""Messages received from the public contact and reservation forms."""

from datetime import datetime

from app.constants import (
    CONTACT_MESSAGE_MAX_LENGTH,
    CONTACT_NAME_MAX_LENGTH,
    CONTACT_SUBJECT_MAX_LENGTH,
    CONTACT_USER_AGENT_MAX_LENGTH,
    EMAIL_MAX_LENGTH,
    IP_MAX_LENGTH,
    PHONE_MAX_LENGTH,
)
from app.database import db
from app.models.base import BigInt
from app.timeutil import now_lima

MESSAGE_STATUSES = ("new", "read", "replied", "archived")

MESSAGE_STATUS_LABELS = {
    "new": "Nuevo",
    "read": "Leído",
    "replied": "Respondido",
    "archived": "Archivado",
}


class ContactMessage(db.Model):
    """Message sent from a public form (table ``contact_messages``)."""

    __tablename__ = "contact_messages"

    id = db.Column(BigInt(), primary_key=True, autoincrement=True)
    name = db.Column(db.String(CONTACT_NAME_MAX_LENGTH), nullable=False)
    mobile = db.Column(db.String(PHONE_MAX_LENGTH), nullable=False)
    email = db.Column(db.String(EMAIL_MAX_LENGTH))
    subject = db.Column(db.String(CONTACT_SUBJECT_MAX_LENGTH))
    message = db.Column(db.Text, nullable=False)
    ip = db.Column(db.String(IP_MAX_LENGTH))
    user_agent = db.Column(db.String(CONTACT_USER_AGENT_MAX_LENGTH))
    status = db.Column(
        db.Enum(*MESSAGE_STATUSES, name="message_status"),
        nullable=False,
        default="new",
        index=True,
    )
    reservation_id = db.Column(
        BigInt(), db.ForeignKey("reservations.id"), nullable=True
    )
    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=now_lima,
        server_default=db.func.current_timestamp(),
        index=True,
    )

    reservation = db.relationship("Reservation", foreign_keys=[reservation_id])

    @property
    def status_label(self):
        return MESSAGE_STATUS_LABELS.get(self.status, self.status)

    def __repr__(self):
        return f"<ContactMessage {self.id}>"
