"""Hotel settings (key/value table)."""

from app.database import db, transaction
from app.models import HotelSetting
from app.models.hotel_setting import DEFAULT_SETTINGS
from app.services.audit_service import log_action


def get_all_settings():
    """Return all settings merged with the defaults."""
    values = dict(DEFAULT_SETTINGS)
    try:
        rows = db.session.scalars(db.select(HotelSetting)).all()
    except Exception:  # pragma: no cover - database unavailable at runtime
        return values
    values.update({row.setting_key: row.setting_value for row in rows})
    return values


def get_setting(key, default=None):
    """Return one setting value."""
    row = db.session.scalars(
        db.select(HotelSetting).filter_by(setting_key=key).limit(1)
    ).first()
    if row is not None and row.setting_value is not None:
        return row.setting_value
    return DEFAULT_SETTINGS.get(key, default)


def save_settings(values, admin_user_id=None):
    """Upsert a mapping of settings and audit the change."""
    with transaction() as session:
        for key, value in values.items():
            row = session.scalars(
                db.select(HotelSetting).filter_by(setting_key=key).limit(1)
            ).first()
            if row is None:
                row = HotelSetting(setting_key=key)
                session.add(row)
            row.setting_value = value
        log_action(
            "settings.update",
            entity="hotel_settings",
            detail=", ".join(sorted(values.keys())),
            admin_user_id=admin_user_id,
        )
    return get_all_settings()


def ensure_default_settings():
    """Create missing default settings rows."""
    changed = False
    for key, value in DEFAULT_SETTINGS.items():
        exists = db.session.scalars(
            db.select(HotelSetting.id).filter_by(setting_key=key).limit(1)
        ).first()
        if exists is None:
            db.session.add(HotelSetting(setting_key=key, setting_value=value))
            changed = True
    if changed:
        db.session.commit()
