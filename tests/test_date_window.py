"""Date strip and horizon tests."""

from datetime import date

from app.services.date_window import (
    PUBLIC_AVAILABILITY_HORIZON_DAYS,
    build_seven_day_strip,
    clamp_date_to_window,
    last_allowed_date,
)


def test_strip_has_seven_days_starting_today() -> None:
    today = date(2026, 11, 10)
    chips = build_seven_day_strip(today)
    assert len(chips) == 7, "strip must contain seven days"
    assert chips[0].iso == "2026-11-10", "first chip must be today"
    assert chips[6].iso == "2026-11-16", "last chip must be today + 6 days"


def test_last_allowed_is_horizon_days_ahead() -> None:
    today = date(2026, 11, 10)
    assert last_allowed_date(today) == date(2026, 12, 10), "horizon must be +30 days"


def test_clamp_inside_and_outside_horizon() -> None:
    today = date(2026, 11, 10)
    last = last_allowed_date(today)
    assert clamp_date_to_window(date(2026, 11, 12), today) == date(2026, 11, 12)
    assert clamp_date_to_window(last, today) == last, "last day of horizon must stay"
    assert clamp_date_to_window(date(2026, 12, 11), today) == today, "day after horizon clamps"
    assert clamp_date_to_window(date(2026, 11, 9), today) == today, "past dates clamp"


def test_horizon_constant() -> None:
    assert PUBLIC_AVAILABILITY_HORIZON_DAYS == 30, "documented horizon is 30 days forward"