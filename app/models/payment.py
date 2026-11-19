"""Payments registered against reservations."""

from app.database import db
from app.models.base import BigInt
from app.timeutil import now_lima

PAYMENT_METHODS = ("cash", "card", "transfer", "yape", "plin")
PAYMENT_STATUSES = ("pending", "completed", "refunded")


class Payment(db.Model):
    """Partial or total payment (table ``payments``)."""

    __tablename__ = "payments"

    id = db.Column(BigInt(), primary_key=True, autoincrement=True)
    reservation_id = db.Column(
        BigInt(), db.ForeignKey("reservations.id"), nullable=False, index=True
    )
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    method = db.Column(
        db.Enum(*PAYMENT_METHODS, name="payment_method"), nullable=False
    )
    status = db.Column(
        db.Enum(*PAYMENT_STATUSES, name="payment_status"),
        nullable=False,
        default="completed",
        index=True,
    )
    reference = db.Column(db.String(80))
    paid_at = db.Column(db.DateTime, nullable=False, default=now_lima, index=True)
    registered_by_admin_id = db.Column(
        BigInt(), db.ForeignKey("admin_users.id"), nullable=True
    )
    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=now_lima,
        server_default=db.func.current_timestamp(),
    )

    reservation = db.relationship("Reservation", back_populates="payments")
    registered_by = db.relationship("AdminUser", foreign_keys=[registered_by_admin_id])

    def __repr__(self):
        return f"<Payment {self.id} {self.amount}>"
