"""Read-only catalog accessors."""

from app.catalog.data import PLACE_TYPES, UNITS
from app.catalog.types import PlaceType, Unit


def list_place_types() -> list[PlaceType]:
    """Return all place types in display order."""
    return list(PLACE_TYPES)


def get_place_type(type_id: str) -> PlaceType:
    """Look up a place type by id; raises ``KeyError`` if missing."""
    for place_type in PLACE_TYPES:
        if place_type.id == type_id:
            return place_type
    raise KeyError(type_id)


def get_unit(unit_id: str) -> Unit:
    """Look up a unit by id; raises ``KeyError`` if missing."""
    for unit in UNITS:
        if unit.id == unit_id:
            return unit
    raise KeyError(unit_id)


def iter_active_units() -> list[Unit]:
    """Return units that accept new bookings."""
    return [unit for unit in UNITS if unit.active]


def units_for_type(type_id: str, *, active_only: bool = True) -> list[Unit]:
    """Return units belonging to a place type."""
    units = [u for u in UNITS if u.type_id == type_id]
    if active_only:
        units = [u for u in units if u.active]
    return units
