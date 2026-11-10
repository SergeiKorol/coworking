"""Public availability aggregation."""

from datetime import date, datetime

from app.extensions import db
from app.models import Booking, BookingStatus
from app.services.availability import build_day_availability


def test_pending_not_shown_as_occupied(flask_app) -> None:
    with flask_app.app_context():
        db.session.add(
            Booking(
                unit_id="room-a",
                starts_at=datetime(2026, 11, 10, 10, 0),
                ends_at=datetime(2026, 11, 10, 11, 0),
                status=BookingStatus.PENDING,
            )
        )
        db.session.commit()
        bookings = Booking.query.all()
        views = build_day_availability(date(2026, 11, 10), bookings)
        meeting = next(view for view in views if view.type_id == "meeting_room")
        slot_10 = next(row for row in meeting.rows if row.label == "10:00–11:00")
        assert "Переговорная A" not in slot_10.occupied_unit_names, (
            "pending booking must not appear on public availability"
        )


def test_confirmed_shown_as_occupied(flask_app) -> None:
    with flask_app.app_context():
        db.session.add(
            Booking(
                unit_id="room-a",
                starts_at=datetime(2026, 11, 10, 10, 0),
                ends_at=datetime(2026, 11, 10, 11, 0),
                status=BookingStatus.CONFIRMED,
            )
        )
        db.session.commit()
        bookings = Booking.query.all()
        views = build_day_availability(date(2026, 11, 10), bookings)
        meeting = next(view for view in views if view.type_id == "meeting_room")
        slot_10 = next(row for row in meeting.rows if row.label == "10:00–11:00")
        assert "Переговорная A" in slot_10.occupied_unit_names, (
            "confirmed booking must mark unit occupied"
        )
