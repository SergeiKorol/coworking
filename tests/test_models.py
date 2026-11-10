"""Database model smoke tests."""

from datetime import datetime

from app.extensions import db
from app.models import Booking, BookingStatus


def test_persist_booking(flask_app) -> None:
    with flask_app.app_context():
        booking = Booking(
            unit_id="room-a",
            starts_at=datetime(2026, 11, 10, 10, 0),
            ends_at=datetime(2026, 11, 10, 12, 0),
            status=BookingStatus.CONFIRMED,
        )
        db.session.add(booking)
        db.session.commit()
        assert booking.id is not None, "booking id must be assigned after commit"
