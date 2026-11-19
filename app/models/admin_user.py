"""Administrator accounts for the /admin panel."""

from werkzeug.security import check_password_hash, generate_password_hash

from app.database import db
from app.models.base import BigInt, TimestampMixin

ADMIN_ROLES = ("admin", "receptionist")


class AdminUser(TimestampMixin, db.Model):
    """Administrator or receptionist account (table ``admin_users``)."""

    __tablename__ = "admin_users"

    id = db.Column(BigInt(), primary_key=True, autoincrement=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(160), nullable=False, unique=True, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(
        db.Enum(*ADMIN_ROLES, name="admin_role"),
        nullable=False,
        default="receptionist",
    )
    active = db.Column(db.Boolean, nullable=False, default=True)
    last_login_at = db.Column(db.DateTime, nullable=True)

    @property
    def is_admin(self):
        return self.role == "admin"

    @property
    def initials(self):
        parts = [part for part in (self.name or "").split() if part]
        return "".join(part[0].upper() for part in parts[:2]) or "AD"

    def set_password(self, password):
        """Store a secure hash, never the plain password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verify a plain password against the stored hash."""
        return bool(self.password_hash) and check_password_hash(
            self.password_hash, password
        )

    def __repr__(self):
        return f"<AdminUser {self.email}>"
