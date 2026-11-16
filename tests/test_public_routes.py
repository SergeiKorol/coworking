"""HTTP tests for public routes."""

from datetime import timedelta

from app.services.clock import today_in_timezone


def test_root_redirects_to_availability(client) -> None:
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 302, "root must redirect to availability"
    assert "/availability" in response.headers["Location"]


def test_availability_redirects_out_of_window(client, flask_app) -> None:
    today = today_in_timezone(flask_app.config["TIMEZONE"])
    future = today + timedelta(days=30)
    response = client.get(f"/availability?date={future.isoformat()}", follow_redirects=False)
    assert response.status_code == 302, "out-of-window date must redirect"
    assert "date=" in response.headers["Location"], "redirect must include date query"


def test_availability_ok(client) -> None:
    response = client.get("/availability")
    assert response.status_code == 200, "availability page must render"
    body = response.data.decode("utf-8")
    assert "Стол 1" in body, "page must list desk units"
    assert "Админ" not in body, "public page must not expose admin link"


def test_admin_bookings_redirect_anonymous(client) -> None:
    response = client.get("/admin/bookings", follow_redirects=False)
    assert response.status_code == 302, "anonymous admin access must redirect to login"
