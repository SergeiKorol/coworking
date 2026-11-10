"""Build public availability view models for a single day."""

from dataclasses import dataclass
from datetime import date, datetime, timedelta

from app.catalog import get_place_type, get_unit, list_place_types, units_for_type
from app.catalog.types import Granularity
from app.models import Booking, BookingStatus
from app.services.time_range import day_end_exclusive, day_start, ranges_overlap


@dataclass(frozen=True)
class SlotRow:
    """One row in the public availability table."""

    label: str
    occupied_unit_names: tuple[str, ...]
    free_count: int
    total_count: int


@dataclass(frozen=True)
class TypeDayView:
    """Availability block for a single place type on one day."""

    type_id: str
    title: str
    rows: tuple[SlotRow, ...]


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


def build_day_availability(
    selected: date,
    bookings: list[Booking],
) -> list[TypeDayView]:
    """
    Compute occupancy per place type for ``selected``.

    Args:
        selected: Calendar day shown on the public page.
        bookings: All bookings from the database (caller may pre-filter by range).
    """
    relevant = _bookings_for_day(bookings, selected)
    views: list[TypeDayView] = []

    for place_type in list_place_types():
        units = units_for_type(place_type.id)
        total = len(units)
        if total == 0:
            continue

        rows: list[SlotRow] = []

        if place_type.granularity == Granularity.HOURLY:
            for hour in range(place_type.hour_start, place_type.hour_end):
                slot_start = datetime(selected.year, selected.month, selected.day, hour)
                slot_end = slot_start + timedelta(hours=1)
                occupied: list[str] = []
                for unit in units:
                    if any(
                        b.unit_id == unit.id
                        and ranges_overlap(b.starts_at, b.ends_at, slot_start, slot_end)
                        for b in relevant
                    ):
                        occupied.append(unit.display_name)
                label = f"{hour:02d}:00–{hour + 1:02d}:00"
                rows.append(
                    SlotRow(
                        label=label,
                        occupied_unit_names=tuple(occupied),
                        free_count=total - len(occupied),
                        total_count=total,
                    )
                )
        else:
            d_start = day_start(selected)
            d_end = day_end_exclusive(selected)
            occupied: list[str] = []
            for unit in units:
                if any(
                    b.unit_id == unit.id
                    and ranges_overlap(b.starts_at, b.ends_at, d_start, d_end)
                    for b in relevant
                ):
                    occupied.append(unit.display_name)
            label = "Весь день" if place_type.granularity == Granularity.DAILY else "Месяц (на этот день)"
            rows.append(
                SlotRow(
                    label=label,
                    occupied_unit_names=tuple(occupied),
                    free_count=total - len(occupied),
                    total_count=total,
                )
            )

        views.append(
            TypeDayView(
                type_id=place_type.id,
                title=place_type.title,
                rows=tuple(rows),
            )
        )

    return views
