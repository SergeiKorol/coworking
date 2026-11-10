"""Booking validation and conflict rules."""

from datetime import datetime

import pytest

from app.extensions import db
from app.models import Booking, BookingStatus
from app.services.booking_validation import assert_can_save_booking


@pytest.fixture
def room_booking_id(flask_app) -> int:
    with flask_app.app_context():
        booking = Booking(
            unit_id="room-a",
            starts_at=datetime(2026, 11, 10, 10, 0),
            ends_at=datetime(2026, 11, 10, 12, 0),
            status=BookingStatus.PENDING,
        )
        db.session.add(booking)
        db.session.commit()
        return booking.id


def test_rejects_overlap_same_unit(flask_app, room_booking_id: int) -> None:
    with flask_app.app_context():
        result = assert_can_save_booking(
            unit_id="room-a",
            starts_at=datetime(2026, 11, 10, 11, 0),
            ends_at=datetime(2026, 11, 10, 13, 0),
            status=BookingStatus.CONFIRMED,
        )
        assert result.ok is False, "overlapping pending booking must block save"
        assert result.errors, "validation must return error messages"


def test_cancelled_does_not_block(flask_app, room_booking_id: int) -> None:
    with flask_app.app_context():
        existing = db.session.get(Booking, room_booking_id)
        existing.status = BookingStatus.CANCELLED
        db.session.commit()
        result = assert_can_save_booking(
            unit_id="room-a",
            starts_at=datetime(2026, 11, 10, 11, 0),
            ends_at=datetime(2026, 11, 10, 13, 0),
            status=BookingStatus.CONFIRMED,
        )
        assert result.ok is True, "cancelled booking must not block the slot"
