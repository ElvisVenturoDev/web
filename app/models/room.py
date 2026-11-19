"""Physical hotel rooms."""

from app.database import db
from app.models.base import BigInt, TimestampMixin

ROOM_STATUSES = ("available", "occupied", "maintenance", "cleaning")


class Room(TimestampMixin, db.Model):
    """Physical room that can be assigned to a reservation."""

    __tablename__ = "rooms"

    id = db.Column(BigInt(), primary_key=True, autoincrement=True)
    room_number = db.Column(db.String(10), nullable=False, unique=True)
    room_type_id = db.Column(
        BigInt(), db.ForeignKey("room_types.id"), nullable=False, index=True
    )
    floor = db.Column(db.SmallInteger)
    status = db.Column(
        db.Enum(*ROOM_STATUSES, name="room_status"),
        nullable=False,
        default="available",
        index=True,
    )
    notes = db.Column(db.String(255))
    active = db.Column(db.Boolean, nullable=False, default=True, index=True)

    room_type = db.relationship("RoomType", back_populates="rooms")
    reservations = db.relationship("Reservation", back_populates="room")

    def __repr__(self):
        return f"<Room {self.room_number}>"
