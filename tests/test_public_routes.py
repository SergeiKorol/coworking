"""HTTP tests for public routes."""

from datetime import date, timedelta

from app.services.clock import today_in_timezone


def test_availability_redirects_out_of_window(client, flask_app) -> None:
    today = today_in_timezone(flask_app.config["TIMEZONE"])
    future = today + timedelta(days=30)
    response = client.get(f"/availability?date={future.isoformat()}", follow_redirects=False)
    assert response.status_code == 302, "out-of-window date must redirect"
    assert "date=" in response.headers["Location"], "redirect must include date query"


def test_availability_ok(client) -> None:
    response = client.get("/availability")
    assert response.status_code == 200, "availability page must render"
    assert "Переговорные".encode() in response.data, "page must list meeting room section"


def test_admin_bookings_redirect_anonymous(client) -> None:
    response = client.get("/admin/bookings", follow_redirects=False)
    assert response.status_code == 302, "anonymous admin access must redirect to login"
