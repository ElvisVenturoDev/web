"""Lima business timezone helpers.

Booking dates are stored as ``DATE`` and every timestamp is stored as a naive
``DATETIME`` already expressed in America/Lima. This keeps the data readable
from JavaFX without timezone conversions and matches the MySQL server timezone
configured in docker-compose.yml.
"""

from datetime import date, datetime
from zoneinfo import ZoneInfo

from app.config import get_timezone_name

LIMA = ZoneInfo(get_timezone_name())


def now_lima():
    """Return the current Lima datetime as a naive value for DATETIME columns."""
    return datetime.now(LIMA).replace(tzinfo=None, microsecond=0)


def today_lima():
    """Return today's date in Lima."""
    return datetime.now(LIMA).date()


def parse_date(value):
    """Parse an ISO date string, returning ``None`` when invalid."""
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value))
    except (TypeError, ValueError):
        return None


def nights_between(check_in, check_out):
    """Return the number of nights between two dates (never negative)."""
    if not check_in or not check_out:
        return 0
    return max(0, (check_out - check_in).days)
