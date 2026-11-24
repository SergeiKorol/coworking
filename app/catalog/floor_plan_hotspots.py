"""Pixel hotspots on the floor plan raster (viewBox 1645 x 956)."""

from dataclasses import dataclass


@dataclass(frozen=True)
class DeskHotspot:
    """Circle overlay aligned to desk number badges on ``floor_plan.png``."""

    unit_id: str
    cx: float
    cy: float
    radius: float = 26.0


@dataclass(frozen=True)
class MeetingTableHotspot:
    """Meeting room table fill and caption overlay in viewBox coordinates."""

    unit_id: str = "meeting-room"
    x: float = 95.0
    y: float = 423.0
    width: float = 500.0
    height: float = 115.0
    rx: float = 14.0
    caption_x: float = 345.0
    caption_y: float = 480.0
    caption_font_size: float = 22.0
    caption_line1: str = "16кв.м"
    caption_line2: str = "10 посадочных мест"


FLOOR_PLAN_VIEWBOX_WIDTH = 1645
FLOOR_PLAN_VIEWBOX_HEIGHT = 956

DESK_HOTSPOTS: tuple[DeskHotspot, ...] = (
    DeskHotspot("desk-1", cx=735.9, cy=430.2),
    DeskHotspot("desk-2", cx=735.9, cy=630.6),
    DeskHotspot("desk-3", cx=1065.1, cy=630.6),
    DeskHotspot("desk-4", cx=1065.1, cy=430.2),
    DeskHotspot("desk-5", cx=1190.4, cy=430.2),
    DeskHotspot("desk-6", cx=1190.4, cy=630.6),
    DeskHotspot("desk-7", cx=1505.7, cy=630.6),
    DeskHotspot("desk-8", cx=1505.7, cy=430.2),
)

MEETING_TABLE_HOTSPOT = MeetingTableHotspot()