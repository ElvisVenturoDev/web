"""Availability and overlap rules shared by web, admin and JavaFX clients.

Every overlap check is executed over the same tables. The MySQL queries use
``SELECT ... FOR UPDATE`` so two clients cannot confirm the same room at the
same time.
"""

from sqlalchemy import and_, func, or_

from app.database import db
from app.models import ACTIVE_RESERVATION_STATUSES, Reservation, Room, RoomType


def _overlap_condition(check_in, check_out, exclude_id=None):
    conditions = [
        Reservation.status.in_(ACTIVE_RESERVATION_STATUSES),
        Reservation.check_in < check_out,
        Reservation.check_out > check_in,
    ]
    if exclude_id is not None:
        conditions.append(Reservation.id != exclude_id)
    return and_(*conditions)


def overlapping_query(check_in, check_out, exclude_id=None):
    """Base query of active overlapping reservations."""
    return db.select(Reservation.id).where(
        _overlap_condition(check_in, check_out, exclude_id)
    )


def room_is_free(room_id, check_in, check_out, exclude_id=None, lock=False):
    """Whether a physical room has no active overlap in the date range."""
    room = db.session.get(Room, room_id)
    if room is None:
        return False
    if lock:
        db.session.execute(
            db.select(Room.id).where(Room.id == room_id).with_for_update()
        ).scalar()
    count = db.session.scalar(
        db.select(func.count(Reservation.id)).where(
            Reservation.room_id == room_id,
            _overlap_condition(check_in, check_out, exclude_id),
        )
    )
    return (count or 0) == 0


def usable_room_count(room_type_id):
    """Active rooms of a type that are not in maintenance."""
    return (
        db.session.scalar(
            db.select(func.count(Room.id)).where(
                Room.room_type_id == room_type_id,
                Room.active.is_(True),
                Room.status != "maintenance",
            )
        )
        or 0
    )


def room_type_available(room_type_id, check_in, check_out, exclude_id=None):
    """Check room-type capacity against active overlapping reservations.

    Unassigned reservations still consume capacity, so the type is available
    only while overlaps are below the number of usable physical rooms.
    """
    usable = usable_room_count(room_type_id)
    if usable <= 0:
        return False
    overlapping = (
        db.session.scalar(
            db.select(func.count(Reservation.id)).where(
                Reservation.room_type_id == room_type_id,
                _overlap_condition(check_in, check_out, exclude_id),
            )
        )
        or 0
    )
    return overlapping < usable


def find_free_room(room_type_id, check_in, check_out, exclude_id=None):
    """Return the first free, active, non-maintenance room of a type."""
    rooms = db.session.scalars(
        db.select(Room)
        .where(
            Room.room_type_id == room_type_id,
            Room.active.is_(True),
            Room.status != "maintenance",
        )
        .order_by(Room.room_number)
        .with_for_update()
    ).all()
    for room in rooms:
        if room_is_free(room.id, check_in, check_out, exclude_id=exclude_id):
            return room
    return None


def available_room_types(check_in, check_out, adults=1, children=0):
    """Room types that fit the party and have capacity for the range."""
    types = db.session.scalars(
        db.select(RoomType)
        .where(RoomType.active.is_(True))
        .order_by(RoomType.base_price)
    ).all()
    result = []
    for room_type in types:
        if (room_type.capacity_adults or 0) < adults:
            continue
        if (room_type.capacity_children or 0) < children:
            continue
        if room_type_available(room_type.id, check_in, check_out):
            result.append(room_type)
    return result


def busy_map(check_in, check_out):
    """Map ``(room_id, date)`` to the blocking reservation for a calendar."""
    rows = db.session.execute(
        db.select(
            Reservation.room_id,
            Reservation.check_in,
            Reservation.check_out,
            Reservation.code,
            Reservation.status,
        ).where(
            Reservation.room_id.is_not(None),
            Reservation.status.in_(ACTIVE_RESERVATION_STATUSES),
            Reservation.check_in < check_out,
            Reservation.check_out > check_in,
        )
    ).all()
    busy = {}
    from datetime import timedelta

    for room_id, start, end, code, status in rows:
        current = start
        while current < end:
            busy[(room_id, current)] = {"code": code, "status": status}
            current += timedelta(days=1)
    return busy
