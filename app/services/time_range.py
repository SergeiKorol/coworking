"""Datetime interval helpers for bookings and availability."""

from datetime import date, datetime, timedelta


def ranges_overlap(
    a_start: datetime,
    a_end: datetime,
    b_start: datetime,
    b_end: datetime,
) -> bool:
    """
    Return True when half-open intervals ``[a_start, a_end)`` and ``[b_start, b_end)`` intersect.
    """
    return a_start < b_end and b_start < a_end


def day_start(d: date) -> datetime:
    """Local naive midnight at the start of calendar day ``d``."""
    return datetime(d.year, d.month, d.day)


def day_end_exclusive(d: date) -> datetime:
    """Local naive midnight at the start of the day after ``d``."""
    return day_start(d) + timedelta(days=1)


def month_bounds(year: int, month: int) -> tuple[datetime, datetime]:
    """
    Return ``[starts_at, ends_at)`` for a calendar month in local naive time.
    """
    start = datetime(year, month, 1)
    if month == 12:
        end = datetime(year + 1, 1, 1)
    else:
        end = datetime(year, month + 1, 1)
    return start, end
