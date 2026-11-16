"""CSS overlay marker positions on the floor plan image (percent of container)."""

from dataclasses import dataclass


@dataclass(frozen=True)
class OverlayMarker:
    """Absolute position for a unit status badge on the floor plan."""

    unit_id: str
    top_pct: float
    left_pct: float


# Tuned for floor-plan.png from the reference mock; adjust after asset swap.
FLOOR_OVERLAY_MARKERS: tuple[OverlayMarker, ...] = (
    OverlayMarker("meeting-room", top_pct=20.0, left_pct=16.0),
    OverlayMarker("desk-1", top_pct=41.0, left_pct=42.0),
    OverlayMarker("desk-2", top_pct=60.0, left_pct=42.0),
    OverlayMarker("desk-3", top_pct=60.0, left_pct=58.0),
    OverlayMarker("desk-4", top_pct=41.0, left_pct=58.0),
    OverlayMarker("desk-5", top_pct=41.0, left_pct=72.0),
    OverlayMarker("desk-6", top_pct=60.0, left_pct=72.0),
    OverlayMarker("desk-7", top_pct=60.0, left_pct=86.0),
    OverlayMarker("desk-8", top_pct=41.0, left_pct=86.0),
)
