"""Build public availability view models for a single day."""

from dataclasses import dataclass
from datetime import date

from app.catalog import get_unit
from app.catalog.data import PUBLIC_UNIT_ORDER
from app.models import Booking, BookingStatus
from app.services.time_range import day_end_exclusive, day_start, ranges_overlap


@dataclass(frozen=True)
class UnitStatus:
    """Occupancy for one catalog unit on a single calendar day."""

    unit_id: str
    display_name: str
    type_id: str
    occupied: bool


def _confirmed_for_public(booking: Booking) -> bool:
    """Only confirmed bookings reduce public availability."""
    return booking.status == BookingStatus.CONFIRMED


def _bookings_for_day(bookings: list[Booking], selected: date) -> list[Booking]:
    """Filter bookings overlapping the selected calendar day."""
    d_start = day_start(selected)
    d_end = day_end_exclusive(selected)
    return [
        booking
        for booking in bookings
        if _confirmed_for_public(booking)
        and ranges_overlap(booking.starts_at, booking.ends_at, d_start, d_end)
    ]


def build_day_unit_statuses(
    selected: date,
    bookings: list[Booking],
) -> list[UnitStatus]:
    """
    Compute per-unit occupied flag for the public availability page.

    Units follow ``PUBLIC_UNIT_ORDER``; unknown units in DB are ignored here.
    """
    relevant = _bookings_for_day(bookings, selected)
    d_start = day_start(selected)
    d_end = day_end_exclusive(selected)
    statuses: list[UnitStatus] = []

    for unit_id in PUBLIC_UNIT_ORDER:
        unit = get_unit(unit_id)
        occupied = any(
            booking.unit_id == unit_id
            and ranges_overlap(booking.starts_at, booking.ends_at, d_start, d_end)
            for booking in relevant
        )
        statuses.append(
            UnitStatus(
                unit_id=unit.id,
                display_name=unit.display_name,
                type_id=unit.type_id,
                occupied=occupied,
            )
        )
    return statuses
