"""Application SQLAlchemy models.

The legacy dairy-commerce models (products, inventory, sales, customers) are
retired from the runtime registry. They remain on disk as reference only; the
hotel schema below is the single source of truth for web and JavaFX.
"""

from app.models.admin_user import AdminUser
from app.models.audit_log import AuditLog
from app.models.contact_message import ContactMessage, MESSAGE_STATUSES
from app.models.guest import Guest
from app.models.hotel_setting import HotelSetting
from app.models.payment import Payment
from app.models.reservation import (
    ACTIVE_RESERVATION_STATUSES,
    RESERVATION_SOURCES,
    RESERVATION_STATUSES,
    Reservation,
)
from app.models.room import ROOM_STATUSES, Room
from app.models.room_type import RoomType

__all__ = [
    "AdminUser",
    "AuditLog",
    "ContactMessage",
    "Guest",
    "HotelSetting",
    "MESSAGE_STATUSES",
    "Payment",
    "Reservation",
    "Room",
    "RoomType",
    "ACTIVE_RESERVATION_STATUSES",
    "RESERVATION_SOURCES",
    "RESERVATION_STATUSES",
    "ROOM_STATUSES",
]
