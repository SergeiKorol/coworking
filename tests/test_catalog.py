"""Catalog seed tests."""

from app.catalog import get_unit, list_place_types


def test_catalog_has_meeting_room_type() -> None:
    types = list_place_types()
    ids = {place_type.id for place_type in types}
    assert "meeting_room" in ids, "seed must include meeting_room type"


def test_unit_links_to_type() -> None:
    unit = get_unit("room-a")
    assert unit.type_id == "meeting_room", "room-a must belong to meeting_room"
    assert unit.active is True, "room-a must be active in v1 seed"
