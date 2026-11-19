"""Hotel guests, reused by document number or email."""

from app.database import db
from app.models.base import BigInt, TimestampMixin


class Guest(TimestampMixin, db.Model):
    """Guest profile (table ``guests``)."""

    __tablename__ = "guests"

    id = db.Column(BigInt(), primary_key=True, autoincrement=True)
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)
    document_type = db.Column(db.String(20))
    document_number = db.Column(db.String(30), unique=True, nullable=True)
    email = db.Column(db.String(160), nullable=True, index=True)
    phone = db.Column(db.String(30), nullable=False, index=True)
    nationality = db.Column(db.String(60))
    notes = db.Column(db.Text)

    reservations = db.relationship("Reservation", back_populates="guest")

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def __repr__(self):
        return f"<Guest {self.full_name}>"
