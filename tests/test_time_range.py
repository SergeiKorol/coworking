"""Interval overlap tests."""

from datetime import datetime

from app.services.time_range import ranges_overlap


def test_ranges_overlap_half_open() -> None:
    a_start = datetime(2026, 11, 10, 10, 0)
    a_end = datetime(2026, 11, 10, 12, 0)
    b_start = datetime(2026, 11, 10, 11, 0)
    b_end = datetime(2026, 11, 10, 13, 0)
    assert ranges_overlap(a_start, a_end, b_start, b_end) is True, "overlapping intervals"


def test_ranges_no_touch_at_boundary() -> None:
    a_start = datetime(2026, 11, 10, 10, 0)
    a_end = datetime(2026, 11, 10, 11, 0)
    b_start = datetime(2026, 11, 10, 11, 0)
    b_end = datetime(2026, 11, 10, 12, 0)
    assert ranges_overlap(a_start, a_end, b_start, b_end) is False, "touching at end boundary"
