"""Public availability page — PNG-in-SVG floor plan hotspots."""

from datetime import datetime, timedelta

from app.extensions import db
from app.models import Booking, BookingStatus
from app.services.clock import today_in_timezone


def test_availability_uses_svg_not_png_overlay(client) -> None:
    response = client.get("/availability")
    assert response.status_code == 200, "availability must render"
    body = response.data.decode("utf-8")
    assert "floor-plan-svg" in body, "page must embed SVG floor plan"
    assert "floor-overlay-marker" not in body, "legacy CSS overlays must be removed"
    assert "floor_plan.png" in body, "svg must embed the floor plan raster"
    assert "floor-plan-img" not in body, "standalone img tag must not be used"
    assert "id=\"floor-decor\"" not in body, "vector decor must not replace the png"
    assert 'data-unit-id="desk-1"' in body, "desk groups must be addressable"
    assert 'data-unit-id="meeting-room"' in body, "meeting room group must exist"


def test_desk_free_by_default_has_free_class(client) -> None:
    response = client.get("/availability")
    body = response.data.decode("utf-8")
    assert 'data-unit-id="desk-1"' in body
    idx = body.index('data-unit-id="desk-1"')
    snippet = body[max(0, idx - 120) : idx + 120]
    assert "floor-unit--free" in snippet, "unbooked desk must be free on the plan"


def test_confirmed_desk_shows_busy_class(client, flask_app) -> None:
    today = today_in_timezone(flask_app.config["TIMEZONE"])
    with flask_app.app_context():
        db.session.add(
            Booking(
                unit_id="desk-2",
                starts_at=datetime.combine(today, datetime.min.time()),
                ends_at=datetime.combine(today, datetime.min.time()) + timedelta(days=1),
                status=BookingStatus.CONFIRMED,
            )
        )
        db.session.commit()
    response = client.get(f"/availability?date={today.isoformat()}")
    body = response.data.decode("utf-8")
    idx = body.index('data-unit-id="desk-2"')
    snippet = body[max(0, idx - 120) : idx + 120]
    assert "floor-unit--busy" in snippet, "confirmed booking must mark desk busy on SVG"


def test_cards_still_present(client) -> None:
    response = client.get("/availability")
    body = response.data.decode("utf-8")
    assert "unit-card" in body, "unit cards must remain under the plan"
    assert "Стол 1" in body, "card titles must still list desks"