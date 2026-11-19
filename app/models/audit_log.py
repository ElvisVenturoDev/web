"""Audit trail for sensitive administrator actions."""

from app.database import db
from app.models.base import BigInt
from app.timeutil import now_lima


class AuditLog(db.Model):
    """One audited action (table ``audit_log``)."""

    __tablename__ = "audit_log"

    id = db.Column(BigInt(), primary_key=True, autoincrement=True)
    admin_user_id = db.Column(
        BigInt(), db.ForeignKey("admin_users.id"), nullable=True, index=True
    )
    action = db.Column(db.String(80), nullable=False, index=True)
    entity = db.Column(db.String(80))
    entity_id = db.Column(BigInt(), nullable=True)
    detail = db.Column(db.Text)
    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=now_lima,
        server_default=db.func.current_timestamp(),
        index=True,
    )

    admin_user = db.relationship("AdminUser")

    def __repr__(self):
        return f"<AuditLog {self.action}>"
