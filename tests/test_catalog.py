"""Catalog seed tests."""

from app.catalog import get_unit, list_place_types


def test_catalog_has_meeting_room_type() -> None:
    types = list_place_types()
    ids = {place_type.id for place_type in types}
    assert "meeting_room" in ids, "seed must include meeting_room type"
    assert "dedicated_desk" not in ids, "monthly desk type must be removed in v2"


def test_unit_links_to_type() -> None:
    unit = get_unit("meeting-room")
    assert unit.type_id == "meeting_room", "meeting-room must belong to meeting_room"
    assert get_unit("desk-1").type_id == "hot_desk"
