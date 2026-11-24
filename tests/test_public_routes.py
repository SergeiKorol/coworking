"""HTTP tests for public routes."""

from datetime import timedelta
from pathlib import Path

from app.services.clock import today_in_timezone
from app.services.date_window import last_allowed_date


def test_root_redirects_to_availability(client) -> None:
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 302, "root must redirect to availability"
    assert "/availability" in response.headers["Location"]


def test_availability_redirects_out_of_window(client, flask_app) -> None:
    today = today_in_timezone(flask_app.config["TIMEZONE"])
    beyond = last_allowed_date(today) + timedelta(days=1)
    response = client.get(f"/availability?date={beyond.isoformat()}", follow_redirects=False)
    assert response.status_code == 302, "out-of-window date must redirect"
    assert "date=" in response.headers["Location"], "redirect must include date query"


def test_availability_last_horizon_day_ok(client, flask_app) -> None:
    today = today_in_timezone(flask_app.config["TIMEZONE"])
    last = last_allowed_date(today)
    response = client.get(f"/availability?date={last.isoformat()}")
    assert response.status_code == 200, "last horizon day must render"


def test_availability_includes_calendar_ui(client) -> None:
    response = client.get("/availability")
    body = response.data.decode("utf-8")
    assert "availability-date-toolbar" in body, "date toolbar must wrap chips and calendar"
    assert "availability-month-calendar" not in body, "month grid must be removed"
    assert 'id="availability-date-picker"' in body, "native date picker must exist"
    assert "Пред. неделя" not in body, "week arrows must be removed"
    assert 'id="availability-calendar-open"' in body, "calendar button required"


def test_public_header_css_shows_logo_row_on_mobile() -> None:
    css_path = (
        Path(__file__).resolve().parent.parent / "app/static/css/availability-v2.css"
    )
    css = css_path.read_text(encoding="utf-8")
    assert "site-header__row-mobile" in css, "mobile header must use logo row"
    assert ".site-header__logo" in css
    logo_hide = ".site-header__logo" in css and "display: none" in css.split(
        ".site-header__logo"
    )[1][:80]
    assert not logo_hide, "mobile header must not hide logo"
    mobile_css = css.split("@media (max-width: 768px)", 1)[1]
    contacts_rule = mobile_css.split(".site-header__contacts", 1)[1].split("}", 1)[0]
    assert "flex-direction: column" in contacts_rule, (
        "mobile contacts must stack address over phone"
    )
    address_rule = mobile_css.split(".site-header__address", 1)[1].split("}", 1)[0]
    assert "white-space: nowrap" not in address_rule, (
        "address must wrap on mobile, not single-line ellipsis"
    )


def test_availability_includes_meeting_caption(client) -> None:
    response = client.get("/availability")
    body = response.data.decode("utf-8")
    assert "floor-unit__caption" in body, "meeting caption must render on floor plan"
    assert "16кв.м" in body
    assert "site-header__row-mobile" in body


def test_availability_ok(client) -> None:
    response = client.get("/availability")
    assert response.status_code == 200, "availability page must render"
    body = response.data.decode("utf-8")
    assert "Стол 1" in body, "page must list desk units"
    assert "Админ" not in body, "public page must not expose admin link"


def test_admin_bookings_redirect_anonymous(client) -> None:
    response = client.get("/admin/bookings", follow_redirects=False)
    assert response.status_code == 302, "anonymous admin access must redirect to login"
