"""Reservations: the core entity shared with the JavaFX client."""

from decimal import Decimal

from sqlalchemy import CheckConstraint, Index

from app.database import db
from app.models.base import BigInt, TimestampMixin
from app.timeutil import nights_between

RESERVATION_STATUSES = (
    "pending",
    "confirmed",
    "checked_in",
    "checked_out",
    "cancelled",
    "no_show",
)
ACTIVE_RESERVATION_STATUSES = ("pending", "confirmed", "checked_in")
RESERVATION_SOURCES = ("web", "admin", "desktop")


class Reservation(TimestampMixin, db.Model):
    """Booking with a unique human-readable code (table ``reservations``)."""

    __tablename__ = "reservations"
    __table_args__ = (
        CheckConstraint("check_out > check_in", name="ck_reservation_dates"),
        Index("ix_reservations_room_dates", "room_id", "check_in", "check_out"),
        Index(
            "ix_reservations_room_type_dates", "room_type_id", "check_in", "check_out"
        ),
    )

    id = db.Column(BigInt(), primary_key=True, autoincrement=True)
    code = db.Column(db.String(20), nullable=False, unique=True, index=True)
    guest_id = db.Column(
        BigInt(), db.ForeignKey("guests.id"), nullable=False, index=True
    )
    room_type_id = db.Column(
        BigInt(), db.ForeignKey("room_types.id"), nullable=False, index=True
    )
    room_id = db.Column(BigInt(), db.ForeignKey("rooms.id"), nullable=True, index=True)
    check_in = db.Column(db.Date, nullable=False, index=True)
    check_out = db.Column(db.Date, nullable=False, index=True)
    adults = db.Column(db.SmallInteger, nullable=False, default=1)
    children = db.Column(db.SmallInteger, nullable=False, default=0)
    status = db.Column(
        db.Enum(*RESERVATION_STATUSES, name="reservation_status"),
        nullable=False,
        default="pending",
        index=True,
    )
    source = db.Column(
        db.Enum(*RESERVATION_SOURCES, name="reservation_source"),
        nullable=False,
        default="web",
        index=True,
    )
    nightly_rate = db.Column(db.Numeric(10, 2), nullable=False)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    deposit_amount = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    notes = db.Column(db.Text)
    created_by_admin_id = db.Column(
        BigInt(), db.ForeignKey("admin_users.id"), nullable=True
    )

    guest = db.relationship("Guest", back_populates="reservations")
    room_type = db.relationship("RoomType", back_populates="reservations")
    room = db.relationship("Room", back_populates="reservations")
    created_by = db.relationship("AdminUser", foreign_keys=[created_by_admin_id])
    payments = db.relationship(
        "Payment",
        back_populates="reservation",
        cascade="all, delete-orphan",
        order_by="Payment.paid_at",
    )

    @property
    def nights(self):
        return nights_between(self.check_in, self.check_out)

    @property
    def paid_amount(self):
        """Sum of completed payments minus refunded ones."""
        total = Decimal("0.00")
        for payment in self.payments:
            if payment.status == "completed":
                total += Decimal(payment.amount)
            elif payment.status == "refunded":
                total -= Decimal(payment.amount)
        return total

    @property
    def balance(self):
        return Decimal(self.total_amount or 0) - self.paid_amount

    @property
    def is_active(self):
        return self.status in ACTIVE_RESERVATION_STATUSES

    @property
    def status_label(self):
        return STATUS_LABELS.get(self.status, self.status)

    def __repr__(self):
        return f"<Reservation {self.code}>"


STATUS_LABELS = {
    "pending": "Pendiente",
    "confirmed": "Confirmada",
    "checked_in": "En casa",
    "checked_out": "Finalizada",
    "cancelled": "Cancelada",
    "no_show": "No se presentó",
}

SOURCE_LABELS = {"web": "Web", "admin": "Administración", "desktop": "Escritorio"}

PAYMENT_METHOD_LABELS = {
    "cash": "Efectivo",
    "card": "Tarjeta",
    "transfer": "Transferencia",
    "yape": "Yape",
    "plin": "Plin",
}

PAYMENT_STATUS_LABELS = {
    "pending": "Pendiente",
    "completed": "Completado",
    "refunded": "Reembolsado",
}
