"""Booking interval validation and conflict detection."""

from dataclasses import dataclass
from datetime import date, datetime, timedelta

from app.catalog import get_place_type, get_unit
from app.catalog.types import Granularity
from app.extensions import db
from app.models import Booking, BookingStatus
from app.services.time_range import month_bounds, ranges_overlap


@dataclass(frozen=True)
class ValidationResult:
    """Outcome of a booking validation attempt."""

    ok: bool
    errors: tuple[str, ...] = ()


def find_conflicts(
    unit_id: str,
    starts_at: datetime,
    ends_at: datetime,
    exclude_id: int | None = None,
) -> list[Booking]:
    """
    Return bookings on the same unit that overlap the interval, excluding cancelled.

    Args:
        unit_id: Catalog unit identifier.
        starts_at: Proposed interval start (inclusive).
        ends_at: Proposed interval end (exclusive).
        exclude_id: When editing, ignore this booking id.
    """
    query = Booking.query.filter(
        Booking.unit_id == unit_id,
        Booking.status != BookingStatus.CANCELLED,
        Booking.starts_at < ends_at,
        Booking.ends_at > starts_at,
    )
    if exclude_id is not None:
        query = query.filter(Booking.id != exclude_id)
    return list(query.all())


def build_interval_hourly(
    day: date,
    start_hour: int,
    duration_hours: int,
    hour_start: int,
    hour_end: int,
) -> tuple[datetime, datetime] | None:
    """
    Build an hourly booking interval on ``day``.

    Returns None when inputs violate alignment rules.
    """
    if duration_hours < 1:
        return None
    if start_hour < hour_start or start_hour + duration_hours > hour_end:
        return None
    starts_at = datetime(day.year, day.month, day.day, start_hour)
    ends_at = starts_at + timedelta(hours=duration_hours)
    return starts_at, ends_at


def build_interval_daily(start_day: date, end_day: date) -> tuple[datetime, datetime] | None:
    """Build ``[start_day 00:00, day after end_day 00:00)``."""
    if end_day < start_day:
        return None
    starts_at = datetime(start_day.year, start_day.month, start_day.day)
    end_exclusive = end_day + timedelta(days=1)
    ends_at = datetime(end_exclusive.year, end_exclusive.month, end_exclusive.day)
    return starts_at, ends_at


def build_interval_monthly(year: int, month: int) -> tuple[datetime, datetime]:
    """Build a calendar-month interval."""
    return month_bounds(year, month)


def assert_can_save_booking(
    unit_id: str,
    starts_at: datetime,
    ends_at: datetime,
    status: BookingStatus,
    exclude_id: int | None = None,
) -> ValidationResult:
    """
    Validate unit, interval shape, and conflicts before persisting a booking.
    """
    errors: list[str] = []

    try:
        unit = get_unit(unit_id)
    except KeyError:
        return ValidationResult(ok=False, errors=("Неизвестная единица.",))

    if not unit.active:
        errors.append("Единица недоступна для новых броней.")

    if ends_at <= starts_at:
        errors.append("Время окончания должно быть позже времени начала.")

    place_type = get_place_type(unit.type_id)
    if place_type.granularity == Granularity.HOURLY:
        if starts_at.minute != 0 or starts_at.second != 0:
            errors.append("Почасовая бронь должна начинаться на границе часа.")
        if (ends_at - starts_at) % timedelta(hours=1) != timedelta():
            errors.append("Почасовая бронь должна длиться целое число часов.")
        day_cap_end = datetime(
            starts_at.year,
            starts_at.month,
            starts_at.day,
            place_type.hour_end,
        )
        if starts_at.hour < place_type.hour_start or ends_at > day_cap_end:
            errors.append(
                f"Допустимые часы: {place_type.hour_start}:00–{place_type.hour_end}:00."
            )
    elif place_type.granularity == Granularity.DAILY:
        if starts_at.time().isoformat() != "00:00:00" or ends_at.time().isoformat() != "00:00:00":
            errors.append("Дневная бронь должна совпадать с полными календарными днями.")
        if (ends_at - starts_at) % timedelta(days=1) != timedelta():
            errors.append("Дневная бронь должна охватывать целое число дней.")
    elif place_type.granularity == Granularity.MONTHLY:
        month_start, month_end = month_bounds(starts_at.year, starts_at.month)
        if starts_at != month_start or ends_at != month_end:
            errors.append("Месячная бронь должна совпадать с календарным месяцем.")

    conflicts = find_conflicts(unit_id, starts_at, ends_at, exclude_id=exclude_id)
    if conflicts:
        errors.append("Интервал пересекается с другой активной бронью на этом месте.")

    if errors:
        return ValidationResult(ok=False, errors=tuple(errors))
    return ValidationResult(ok=True)


def save_booking(
    unit_id: str,
    starts_at: datetime,
    ends_at: datetime,
    status: BookingStatus,
    note: str | None,
    booking_id: int | None = None,
) -> tuple[Booking | None, ValidationResult]:
    """
    Validate and insert or update a booking row.

    Returns:
        Tuple of (booking or None, validation result).
    """
    result = assert_can_save_booking(
        unit_id,
        starts_at,
        ends_at,
        status,
        exclude_id=booking_id,
    )
    if not result.ok:
        return None, result

    if booking_id is None:
        booking = Booking(
            unit_id=unit_id,
            starts_at=starts_at,
            ends_at=ends_at,
            status=status,
            note=note or None,
        )
        db.session.add(booking)
    else:
        booking = db.session.get(Booking, booking_id)
        if booking is None:
            return None, ValidationResult(ok=False, errors=("Бронь не найдена.",))
        booking.unit_id = unit_id
        booking.starts_at = starts_at
        booking.ends_at = ends_at
        booking.status = status
        booking.note = note or None

    db.session.commit()
    return booking, result
