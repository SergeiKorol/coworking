"""Admin booking edit and status transitions."""

from datetime import date, datetime

from app.extensions import db
from app.models import Booking, BookingStatus


def _login(client) -> None:
    client.post(
        "/admin/login",
        data={"username": "admin", "password": "test-password"},
        follow_redirects=True,
    )


def test_edit_changes_status_from_pending_to_confirmed(client, flask_app) -> None:
    """POST must not be overwritten by _prefill_form (regression)."""
    with flask_app.app_context():
        booking = Booking(
            unit_id="desk-1",
            starts_at=datetime(2026, 11, 19),
            ends_at=datetime(2026, 11, 20),
            status=BookingStatus.PENDING,
        )
        db.session.add(booking)
        db.session.commit()
        booking_id = booking.id

    _login(client)
    response = client.post(
        f"/admin/bookings/{booking_id}/edit",
        data={
            "unit_id": "desk-1",
            "status": BookingStatus.CONFIRMED.value,
            "daily_start": "2026-11-19",
            "daily_end": "2026-11-19",
            "note": "",
            "submit": "Сохранить",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200, "edit form must accept status change"

    with flask_app.app_context():
        updated = db.session.get(Booking, booking_id)
        assert updated is not None
        assert updated.status == BookingStatus.CONFIRMED, (
            "status from POST must persist, not revert to DB prefill"
        )


def test_edit_changes_status_to_cancelled(client, flask_app) -> None:
    with flask_app.app_context():
        booking = Booking(
            unit_id="meeting-room",
            starts_at=datetime(2026, 11, 19),
            ends_at=datetime(2026, 11, 20),
            status=BookingStatus.CONFIRMED,
        )
        db.session.add(booking)
        db.session.commit()
        booking_id = booking.id

    _login(client)
    client.post(
        f"/admin/bookings/{booking_id}/edit",
        data={
            "unit_id": "meeting-room",
            "status": BookingStatus.CANCELLED.value,
            "daily_start": "2026-11-19",
            "daily_end": "2026-11-19",
            "note": "",
            "submit": "Сохранить",
        },
        follow_redirects=True,
    )

    with flask_app.app_context():
        updated = db.session.get(Booking, booking_id)
        assert updated.status == BookingStatus.CANCELLED, "cancelled status must save"