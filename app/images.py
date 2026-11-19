"""Local image routes and upload helpers."""

import uuid
from pathlib import Path

from werkzeug.utils import secure_filename

LOCAL_IMAGES = {
    "hero-1": "/static/img/hero-1.jpg",
    "hero-2": "/static/img/hero-2.jpg",
    "hero-3": "/static/img/hero-3.jpg",
    "room-clasica": "/static/img/room-clasica.jpg",
    "room-superior": "/static/img/room-superior.jpg",
    "room-suite": "/static/img/room-suite.jpg",
    "room-familiar": "/static/img/room-familiar.jpg",
    "room-terraza": "/static/img/room-terraza.jpg",
    "room-deluxe": "/static/img/room-deluxe.jpg",
    "experience": "/static/img/experience.jpg",
    "spa": "/static/img/spa.jpg",
    "lobby": "/static/img/lobby.jpg",
    "photo-1452195100486-9cc805987862": "/static/img/photo-1452195100486-9cc805987862.avif",
    "photo-1486297678162-eb2a19b0a32d": "/static/img/photo-1486297678162-eb2a19b0a32d.avif",
    "photo-1488477181946-6428a0291777": "/static/img/photo-1488477181946-6428a0291777.avif",
    "photo-1500076656116-558758c991c1": "/static/img/photo-1500076656116-558758c991c1.avif",
    "photo-1500595046743-cd271d694d30": "/static/img/photo-1500595046743-cd271d694d30.avif",
    "photo-1550583724-b2692b85b150": "/static/img/photo-1550583724-b2692b85b150.avif",
    "photo-1563636619-e9143da7973b": "/static/img/photo-1563636619-e9143da7973b.avif",
    "photo-1571212515416-fef01fc43637": "/static/img/photo-1571212515416-fef01fc43637.avif",
    "photo-1628088062854-d1870b4553da": "/static/img/photo-1628088062854-d1870b4553da.avif",
}

CATEGORY_IMAGES = {
    "clasica": LOCAL_IMAGES["room-clasica"],
    "superior": LOCAL_IMAGES["room-superior"],
    "suite": LOCAL_IMAGES["room-suite"],
    "familiar": LOCAL_IMAGES["room-familiar"],
    "deluxe": LOCAL_IMAGES["room-deluxe"],
}
DEFAULT_IMAGE = LOCAL_IMAGES["room-clasica"]

ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "avif"}
ROOMS_IMAGE_DIR = Path(__file__).resolve().parent / "static" / "img" / "rooms"


def local_image_url(image_url=None, category=None):
    """Return a local image route, even for old URLs stored in the database."""
    if image_url and image_url.startswith("/static/"):
        return image_url

    if image_url:
        for image_key, local_url in LOCAL_IMAGES.items():
            if image_key in image_url:
                return local_url

    return CATEGORY_IMAGES.get((category or "").lower(), DEFAULT_IMAGE)


def save_room_image(file_storage):
    """Persist an uploaded room image with a unique file name.

    Returns:
        str | None: Public relative URL, or ``None`` when no file was sent.

    Raises:
        ValueError: When the extension is not allowed.
    """
    if file_storage is None or not getattr(file_storage, "filename", ""):
        return None

    original = secure_filename(file_storage.filename)
    extension = original.rsplit(".", 1)[-1].lower() if "." in original else ""
    if extension not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValueError(
            "Formato de imagen no permitido. Usa JPG, PNG, WEBP o AVIF."
        )

    ROOMS_IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    unique_name = f"{uuid.uuid4().hex}.{extension}"
    file_storage.save(ROOMS_IMAGE_DIR / unique_name)
    return f"/static/img/rooms/{unique_name}"
