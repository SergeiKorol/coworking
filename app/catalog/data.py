"""v1 seed data for place types and units (edit + redeploy to change)."""

from app.catalog.types import Granularity, PlaceType, Unit

PLACE_TYPES: tuple[PlaceType, ...] = (
    PlaceType(
        id="meeting_room",
        title="Переговорные",
        granularity=Granularity.HOURLY,
        hour_start=9,
        hour_end=21,
    ),
    PlaceType(
        id="hot_desk",
        title="Столы (день)",
        granularity=Granularity.DAILY,
    ),
    PlaceType(
        id="dedicated_desk",
        title="Столы (месяц)",
        granularity=Granularity.MONTHLY,
    ),
)

UNITS: tuple[Unit, ...] = (
    Unit(id="room-a", type_id="meeting_room", display_name="Переговорная A"),
    Unit(id="room-b", type_id="meeting_room", display_name="Переговорная B"),
    Unit(id="desk-1", type_id="hot_desk", display_name="Стол 1"),
    Unit(id="desk-2", type_id="hot_desk", display_name="Стол 2"),
    Unit(id="desk-month-1", type_id="dedicated_desk", display_name="Стол M1"),
)
