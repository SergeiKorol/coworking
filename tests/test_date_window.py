"""Seven-day strip tests."""

from datetime import date

from app.services.date_window import build_seven_day_strip, clamp_date_to_window


def test_strip_has_seven_days_starting_today() -> None:
    chips = build_seven_day_strip(date(2026, 11, 10))
    assert len(chips) == 7, "strip must contain seven days"
    assert chips[0].iso == "2026-11-10", "first chip must be anchor day"
    assert chips[6].iso == "2026-11-16", "last chip must be anchor + 6 days"


def test_clamp_outside_window() -> None:
    today = date(2026, 11, 10)
    assert clamp_date_to_window(date(2026, 11, 12), today) == date(2026, 11, 12)
    assert clamp_date_to_window(date(2099, 1, 1), today) == today, "far future must clamp"
