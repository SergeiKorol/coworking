"""Public availability aggregation."""

from datetime import date, datetime

from app.extensions import db
from app.models import Booking, BookingStatus
from app.services.availability import build_day_unit_statuses


def test_pending_not_shown_as_occupied(flask_app) -> None:
    with flask_app.app_context():
        db.session.add(
            Booking(
                unit_id="desk-1",
                starts_at=datetime(2026, 11, 10),
                ends_at=datetime(2026, 11, 11),
                status=BookingStatus.PENDING,
            )
        )
        db.session.commit()
        bookings = Booking.query.all()
        statuses = build_day_unit_statuses(date(2026, 11, 10), bookings)
        desk = next(s for s in statuses if s.unit_id == "desk-1")
        assert desk.occupied is False, "pending booking must not mark desk occupied"


def test_confirmed_shown_as_occupied(flask_app) -> None:
    with flask_app.app_context():
        db.session.add(
            Booking(
                unit_id="meeting-room",
                starts_at=datetime(2026, 11, 10),
                ends_at=datetime(2026, 11, 11),
                status=BookingStatus.CONFIRMED,
            )
        )
        db.session.commit()
        bookings = Booking.query.all()
        statuses = build_day_unit_statuses(date(2026, 11, 10), bookings)
        room = next(s for s in statuses if s.unit_id == "meeting-room")
        assert room.occupied is True, "confirmed daily booking must mark meeting room occupied"


def test_eight_desks_and_one_meeting_room(flask_app) -> None:
    with flask_app.app_context():
        statuses = build_day_unit_statuses(date(2026, 11, 10), [])
        assert len(statuses) == 9, "catalog must expose 8 desks and 1 meeting room"
        desk_ids = [s.unit_id for s in statuses if s.type_id == "hot_desk"]
        assert desk_ids == [f"desk-{i}" for i in range(1, 9)]
