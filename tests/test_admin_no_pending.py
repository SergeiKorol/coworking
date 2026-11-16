"""Admin must not create or save bookings as pending."""

from datetime import datetime

from app.extensions import db
from app.models import Booking, BookingStatus


def _login(client) -> None:
    client.post(
        "/admin/login",
        data={"username": "admin", "password": "test-password"},
        follow_redirects=True,
    )


def test_new_booking_always_confirmed(client, flask_app) -> None:
    _login(client)
    response = client.post(
        "/admin/bookings/new",
        data={
            "unit_id": "desk-2",
            "daily_start": "2026-11-20",
            "daily_end": "2026-11-20",
            "note": "",
            "submit": "Сохранить",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200

    with flask_app.app_context():
        booking = (
            Booking.query.filter_by(unit_id="desk-2")
            .order_by(Booking.id.desc())
            .first()
        )
        assert booking is not None
        assert booking.status == BookingStatus.CONFIRMED, (
            "admin create must always persist confirmed"
        )


def test_edit_rejects_pending_status(client, flask_app) -> None:
    with flask_app.app_context():
        booking = Booking(
            unit_id="desk-3",
            starts_at=datetime(2026, 11, 21),
            ends_at=datetime(2026, 11, 22),
            status=BookingStatus.CONFIRMED,
        )
        db.session.add(booking)
        db.session.commit()
        booking_id = booking.id

    _login(client)
    client.post(
        f"/admin/bookings/{booking_id}/edit",
        data={
            "unit_id": "desk-3",
            "status": BookingStatus.PENDING.value,
            "daily_start": "2026-11-21",
            "daily_end": "2026-11-21",
            "note": "",
            "submit": "Сохранить",
        },
        follow_redirects=True,
    )

    with flask_app.app_context():
        updated = db.session.get(Booking, booking_id)
        assert updated.status == BookingStatus.CONFIRMED, (
            "tampered pending POST must not change booking"
        )