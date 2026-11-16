"""v1 seed data for place types and units (edit + redeploy to change)."""

from app.catalog.types import Granularity, PlaceType, Unit

PLACE_TYPES: tuple[PlaceType, ...] = (
    PlaceType(
        id="meeting_room",
        title="Переговорка",
        granularity=Granularity.DAILY,
    ),
    PlaceType(
        id="hot_desk",
        title="Столы",
        granularity=Granularity.DAILY,
    ),
)

UNITS: tuple[Unit, ...] = (
    Unit(id="meeting-room", type_id="meeting_room", display_name="Переговорка"),
    Unit(id="desk-1", type_id="hot_desk", display_name="Стол 1"),
    Unit(id="desk-2", type_id="hot_desk", display_name="Стол 2"),
    Unit(id="desk-3", type_id="hot_desk", display_name="Стол 3"),
    Unit(id="desk-4", type_id="hot_desk", display_name="Стол 4"),
    Unit(id="desk-5", type_id="hot_desk", display_name="Стол 5"),
    Unit(id="desk-6", type_id="hot_desk", display_name="Стол 6"),
    Unit(id="desk-7", type_id="hot_desk", display_name="Стол 7"),
    Unit(id="desk-8", type_id="hot_desk", display_name="Стол 8"),
)

# Public page display order (desks first, then meeting room).
PUBLIC_UNIT_ORDER: tuple[str, ...] = (
    "desk-1",
    "desk-2",
    "desk-3",
    "desk-4",
    "desk-5",
    "desk-6",
    "desk-7",
    "desk-8",
    "meeting-room",
)
