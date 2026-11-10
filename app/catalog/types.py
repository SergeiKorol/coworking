"""Catalog value types for place types and rentable units."""

from dataclasses import dataclass
from enum import Enum


class Granularity(str, Enum):
    """How booking intervals are aligned for a place type."""

    HOURLY = "hourly"
    DAILY = "daily"
    MONTHLY = "monthly"


@dataclass(frozen=True)
class PlaceType:
    """
    Static definition of a category shown on the public availability page.

    Attributes:
        id: Stable identifier referenced by units.
        title: Human-readable section title.
        granularity: hourly, daily, or monthly alignment rules.
        hour_start: First slot hour for hourly types (inclusive).
        hour_end: Hour after the last slot for hourly types (exclusive).
    """

    id: str
    title: str
    granularity: Granularity
    hour_start: int = 9
    hour_end: int = 21


@dataclass(frozen=True)
class Unit:
    """
    Named seat or room instance from the seed catalog.

    Attributes:
        id: Stable identifier stored on ``Booking.unit_id``.
        type_id: Reference to :class:`PlaceType.id`.
        display_name: Label shown on the public site.
        active: When False, new bookings are rejected.
    """

    id: str
    type_id: str
    display_name: str
    active: bool = True
