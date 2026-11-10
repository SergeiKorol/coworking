"""SQLAlchemy models."""

import enum
from datetime import datetime

from app.extensions import db


class BookingStatus(str, enum.Enum):
    """Lifecycle state of a booking created by an administrator."""

    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"


class Booking(db.Model):
    """
    Reservation interval for a single catalog unit.

    Intervals use half-open semantics: ``[starts_at, ends_at)``.
    """

    __tablename__ = "booking"

    id = db.Column(db.Integer, primary_key=True)
    unit_id = db.Column(db.String(64), nullable=False, index=True)
    starts_at = db.Column(db.DateTime, nullable=False)
    ends_at = db.Column(db.DateTime, nullable=False)
    status = db.Column(
        db.Enum(BookingStatus, name="booking_status", native_enum=False),
        nullable=False,
        default=BookingStatus.PENDING,
    )
    note = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    __table_args__ = (
        db.Index("ix_booking_unit_interval", "unit_id", "starts_at", "ends_at"),
    )
