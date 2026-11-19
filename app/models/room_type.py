"""Room types sold by the hotel."""

from app.database import db
from app.models.base import BigInt, TimestampMixin


class RoomType(TimestampMixin, db.Model):
    """Room category with its base price (table ``room_types``)."""

    __tablename__ = "room_types"

    id = db.Column(BigInt(), primary_key=True, autoincrement=True)
    name = db.Column(db.String(80), nullable=False, unique=True)
    slug = db.Column(db.String(80), nullable=False, unique=True)
    description = db.Column(db.Text)
    capacity_adults = db.Column(db.SmallInteger, nullable=False, default=2)
    capacity_children = db.Column(db.SmallInteger, nullable=False, default=0)
    beds = db.Column(db.String(80))
    size_m2 = db.Column(db.SmallInteger)
    base_price = db.Column(db.Numeric(10, 2), nullable=False)
    amenities = db.Column(db.Text)
    image_url = db.Column(db.String(255))
    # Extra columns used by the public catalog without altering its design.
    category = db.Column(db.String(30), nullable=False, default="clasica")
    featured = db.Column(db.Boolean, nullable=False, default=False)
    rating = db.Column(db.Numeric(2, 1), nullable=False, default=4.8)
    active = db.Column(db.Boolean, nullable=False, default=True, index=True)

    rooms = db.relationship(
        "Room", back_populates="room_type", lazy="selectin", order_by="Room.room_number"
    )
    reservations = db.relationship("Reservation", back_populates="room_type")

    @property
    def capacity_total(self):
        return (self.capacity_adults or 0) + (self.capacity_children or 0)

    @property
    def amenities_list(self):
        """Amenities as a Python list; stored as a comma separated TEXT column."""
        if not self.amenities:
            return []
        return [item.strip() for item in self.amenities.split(",") if item.strip()]

    def __repr__(self):
        return f"<RoomType {self.name}>"
