"""Hotel configuration stored as key/value rows readable from JavaFX."""

from app.database import db
from app.models.base import BigInt
from app.timeutil import now_lima

DEFAULT_SETTINGS = {
    "hotel_name": "Miramar Hotel Boutique",
    "address": "Av. La Rivera 245, Huanchaco, Trujillo, Perú",
    "phone": "+51 949 218 640",
    "email": "reservas@miramarhotel.pe",
    "check_in_time": "15:00",
    "check_out_time": "12:00",
    "currency": "PEN",
}


class HotelSetting(db.Model):
    """Hotel setting (table ``hotel_settings``)."""

    __tablename__ = "hotel_settings"

    id = db.Column(BigInt(), primary_key=True, autoincrement=True)
    setting_key = db.Column(db.String(80), nullable=False, unique=True)
    setting_value = db.Column(db.Text)
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=now_lima,
        onupdate=now_lima,
        server_default=db.func.current_timestamp(),
    )

    def __repr__(self):
        return f"<HotelSetting {self.setting_key}>"
