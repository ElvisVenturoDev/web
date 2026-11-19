"""Room types, physical rooms and the public room catalog."""

import re
import unicodedata
from datetime import timedelta
from decimal import Decimal, InvalidOperation

from flask import current_app
from sqlalchemy import func, or_
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.catalog import ROOMS as FALLBACK_ROOMS
from app.database import db, transaction
from app.images import local_image_url, save_room_image
from app.models import Reservation, Room, RoomType
from app.services.audit_service import log_action
from app.timeutil import today_lima

ROOM_CATEGORIES = ("clasica", "superior", "suite", "familiar", "deluxe")
ROOM_STATUS_LABELS = {
    "available": "Disponible",
    "occupied": "Ocupada",
    "maintenance": "Mantenimiento",
    "cleaning": "Limpieza",
}


def slugify(value):
    """Build a URL-safe slug without external dependencies."""
    normalized = unicodedata.normalize("NFKD", value or "")
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii").lower()
    return re.sub(r"[^a-z0-9]+", "-", ascii_value).strip("-")


def _decimal(value, default=None):
    try:
        return Decimal(str(value).replace(",", ".")).quantize(Decimal("0.01"))
    except (InvalidOperation, TypeError, ValueError):
        return default


def _int(value, default=None):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _fallback_catalog():
    """Public catalog used only when MySQL is unreachable."""
    rooms = []
    for item in FALLBACK_ROOMS:
        room = dict(item)
        room["room_type_id"] = None
        rooms.append(room)
    return rooms


def _room_type_public_dict(room_type):
    detail_parts = []
    if room_type.size_m2:
        detail_parts.append(f"{room_type.size_m2} m²")
    if room_type.beds:
        detail_parts.append(room_type.beds)
    return {
        "id": room_type.slug,
        "room_type_id": room_type.id,
        "name": room_type.name,
        "detail": " · ".join(detail_parts),
        "description": room_type.description or "",
        "category": room_type.category or "clasica",
        "price": float(room_type.base_price or 0),
        "featured": bool(room_type.featured),
        "rating": float(room_type.rating or 0),
        "image": local_image_url(room_type.image_url, room_type.category),
        "alt": f"{room_type.name} en Miramar Hotel Boutique",
        "active": bool(room_type.active),
    }


def load_public_rooms():
    """Load active room types for the public site, preserving the design keys.

    Falls back to ``app/catalog.py`` only when MySQL is unavailable, so the
    public pages keep responding during an outage.
    """
    try:
        room_types = db.session.scalars(
            db.select(RoomType)
            .where(RoomType.active.is_(True))
            .order_by(RoomType.id)
        ).all()
    except SQLAlchemyError:
        current_app.logger.exception("No se pudo leer room_types; usando catálogo local")
        return _fallback_catalog()
    return [_room_type_public_dict(room_type) for room_type in room_types]


def list_room_types(include_inactive=False):
    """Return room types ordered by name."""
    stmt = db.select(RoomType).order_by(RoomType.name)
    if not include_inactive:
        stmt = stmt.where(RoomType.active.is_(True))
    return db.session.scalars(stmt).all()


def get_room_type(room_type_id):
    return db.session.get(RoomType, room_type_id)


def room_type_form_values(room_type):
    if room_type is None:
        return {"category": "clasica", "capacity_adults": "2", "capacity_children": "0"}
    return {
        "name": room_type.name,
        "slug": room_type.slug,
        "description": room_type.description or "",
        "capacity_adults": str(room_type.capacity_adults or 1),
        "capacity_children": str(room_type.capacity_children or 0),
        "beds": room_type.beds or "",
        "size_m2": str(room_type.size_m2 or ""),
        "base_price": f"{Decimal(room_type.base_price or 0):.2f}",
        "amenities": room_type.amenities or "",
        "image_url": room_type.image_url or "",
        "category": room_type.category or "clasica",
        "featured": bool(room_type.featured),
        "rating": str(room_type.rating or "4.8"),
        "active": bool(room_type.active),
    }


def normalize_room_type_form(form):
    """Clean room type values from a WTForms object or a mapping."""
    get = form.get if hasattr(form, "get") else lambda key, default=None: getattr(
        form, key, default
    )
    name = " ".join(str(get("name", "") or "").split())
    return {
        "name": name,
        "slug": slugify(get("slug", "") or name),
        "description": str(get("description", "") or "").strip(),
        "capacity_adults": _int(get("capacity_adults"), 1),
        "capacity_children": _int(get("capacity_children"), 0),
        "beds": str(get("beds", "") or "").strip(),
        "size_m2": _int(get("size_m2"), None),
        "base_price": _decimal(get("base_price"), None),
        "amenities": str(get("amenities", "") or "").strip(),
        "image_url": str(get("image_url", "") or "").strip(),
        "category": str(get("category", "") or "clasica").strip().lower(),
        "featured": bool(get("featured", False)),
        "rating": _decimal(get("rating"), Decimal("4.8")),
        "active": bool(get("active", False)),
    }


def validate_room_type(fields, room_type_id=None):
    errors = []
    if not fields["name"]:
        errors.append("Ingresa el nombre del tipo de habitación.")
    if len(fields["name"]) > 80:
        errors.append("El nombre no puede superar 80 caracteres.")
    if not fields["slug"]:
        errors.append("Ingresa un slug válido.")
    if fields["capacity_adults"] is None or fields["capacity_adults"] < 1:
        errors.append("La capacidad de adultos debe ser al menos 1.")
    if (fields["capacity_children"] or 0) < 0:
        errors.append("La capacidad de niños no puede ser negativa.")
    if fields["base_price"] is None or fields["base_price"] <= 0:
        errors.append("Ingresa un precio base mayor que cero.")
    if fields["category"] not in ROOM_CATEGORIES:
        errors.append("Selecciona una categoría válida.")
    duplicate = db.session.scalars(
        db.select(RoomType).where(
            or_(
                func.lower(RoomType.name) == fields["name"].lower(),
                RoomType.slug == fields["slug"],
            ),
            RoomType.id != room_type_id if room_type_id else True,
        ).limit(1)
    ).first()
    if duplicate is not None:
        errors.append("Ya existe un tipo de habitación con ese nombre o slug.")
    return errors


def save_room_type(fields, room_type_id=None, image_file=None, admin_user_id=None):
    """Create or update a room type, including its image upload."""
    with transaction() as session:
        room_type = session.get(RoomType, room_type_id) if room_type_id else RoomType()
        if room_type is None:
            raise ValueError("El tipo de habitación ya no existe.")
        for key in (
            "name",
            "slug",
            "description",
            "capacity_adults",
            "capacity_children",
            "beds",
            "size_m2",
            "base_price",
            "amenities",
            "image_url",
            "category",
            "featured",
            "rating",
            "active",
        ):
            setattr(room_type, key, fields[key])
        uploaded = save_room_image(image_file)
        if uploaded:
            room_type.image_url = uploaded
        if room_type.image_url:
            room_type.image_url = local_image_url(
                room_type.image_url, room_type.category
            )
        if room_type.id is None:
            session.add(room_type)
        session.flush()
        log_action(
            "room_type.save",
            entity="room_types",
            entity_id=room_type.id,
            detail=room_type.name,
            admin_user_id=admin_user_id,
        )
    return room_type


def delete_room_type(room_type_id, admin_user_id=None):
    """Delete a type only when it has no rooms or reservations."""
    with transaction() as session:
        room_type = session.get(RoomType, room_type_id)
        if room_type is None:
            raise ValueError("El tipo de habitación ya no existe.")
        rooms = session.scalar(
            db.select(func.count(Room.id)).where(Room.room_type_id == room_type_id)
        )
        reservations = session.scalar(
            db.select(func.count(Reservation.id)).where(
                Reservation.room_type_id == room_type_id
            )
        )
        if rooms or reservations:
            room_type.active = False
            log_action(
                "room_type.deactivate",
                entity="room_types",
                entity_id=room_type_id,
                detail="Desactivado: tiene habitaciones o reservas asociadas.",
                admin_user_id=admin_user_id,
            )
            return False
        log_action(
            "room_type.delete",
            entity="room_types",
            entity_id=room_type_id,
            detail=room_type.name,
            admin_user_id=admin_user_id,
        )
        session.delete(room_type)
        return True


def list_rooms(search="", status="", room_type_id=None, page=1, per_page=20):
    stmt = db.select(Room).order_by(Room.room_number)
    if search:
        stmt = stmt.where(Room.room_number.ilike(f"%{search.strip()}%"))
    if status:
        stmt = stmt.where(Room.status == status)
    if room_type_id:
        stmt = stmt.where(Room.room_type_id == room_type_id)
    return db.paginate(stmt, page=page, per_page=per_page, error_out=False)


def get_room(room_id):
    return db.session.get(Room, room_id)


def room_form_values(room):
    if room is None:
        return {"status": "available", "floor": "1"}
    return {
        "room_number": room.room_number,
        "room_type_id": str(room.room_type_id),
        "floor": str(room.floor or ""),
        "status": room.status,
        "notes": room.notes or "",
        "active": bool(room.active),
    }


def normalize_room_form(form):
    get = form.get if hasattr(form, "get") else lambda key, default=None: getattr(
        form, key, default
    )
    return {
        "room_number": str(get("room_number", "") or "").strip().upper(),
        "room_type_id": _int(get("room_type_id"), None),
        "floor": _int(get("floor"), None),
        "status": str(get("status", "") or "available"),
        "notes": str(get("notes", "") or "").strip(),
        "active": bool(get("active", False)),
    }


def validate_room(fields, room_id=None):
    errors = []
    valid_statuses = ("available", "occupied", "maintenance", "cleaning")
    if not fields["room_number"]:
        errors.append("Ingresa el número de habitación.")
    if len(fields["room_number"]) > 10:
        errors.append("El número no puede superar 10 caracteres.")
    if fields["status"] not in valid_statuses:
        errors.append("Selecciona un estado válido.")
    room_type = (
        db.session.get(RoomType, fields["room_type_id"])
        if fields["room_type_id"]
        else None
    )
    if room_type is None:
        errors.append("Selecciona un tipo de habitación existente.")
    duplicate = db.session.scalars(
        db.select(Room).where(
            Room.room_number == fields["room_number"],
            Room.id != room_id if room_id else True,
        ).limit(1)
    ).first()
    if duplicate is not None:
        errors.append("Ya existe una habitación con ese número.")
    return errors


def save_room(fields, room_id=None, admin_user_id=None):
    with transaction() as session:
        room = session.get(Room, room_id) if room_id else Room()
        if room is None:
            raise ValueError("La habitación ya no existe.")
        for key in ("room_number", "room_type_id", "floor", "status", "notes", "active"):
            setattr(room, key, fields[key])
        if room.id is None:
            session.add(room)
        session.flush()
        log_action(
            "room.save",
            entity="rooms",
            entity_id=room.id,
            detail=f"Habitación {room.room_number}",
            admin_user_id=admin_user_id,
        )
    return room


def delete_room(room_id, admin_user_id=None):
    """Delete a room without history; deactivate it when it has reservations."""
    with transaction() as session:
        room = session.get(Room, room_id)
        if room is None:
            raise ValueError("La habitación ya no existe.")
        reservations = session.scalar(
            db.select(func.count(Reservation.id)).where(Reservation.room_id == room_id)
        )
        if reservations:
            room.active = False
            log_action(
                "room.deactivate",
                entity="rooms",
                entity_id=room_id,
                detail="Desactivada: tiene reservas asociadas.",
                admin_user_id=admin_user_id,
            )
            return False
        log_action(
            "room.delete",
            entity="rooms",
            entity_id=room_id,
            detail=room.room_number,
            admin_user_id=admin_user_id,
        )
        session.delete(room)
        return True


def availability_calendar(days=30, room_type_id=None):
    """Return a day-by-day occupancy table for the next ``days`` days."""
    from app.services.availability_service import busy_map

    start = today_lima()
    end = start + timedelta(days=days)
    stmt = (
        db.select(Room)
        .where(Room.active.is_(True))
        .order_by(Room.room_number)
        .options(db.selectinload(Room.room_type))
    )
    if room_type_id:
        stmt = stmt.where(Room.room_type_id == room_type_id)
    rooms = db.session.scalars(stmt).all()
    busy = busy_map(start, end)
    dates = [start + timedelta(days=index) for index in range(days)]
    rows = []
    for room in rooms:
        cells = []
        for day in dates:
            info = busy.get((room.id, day))
            if info:
                cells.append({"state": info["status"], "code": info["code"]})
            elif room.status == "maintenance":
                cells.append({"state": "maintenance", "code": ""})
            else:
                cells.append({"state": "free", "code": ""})
        rows.append({"room": room, "cells": cells})
    return dates, rows
