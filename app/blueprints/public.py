"""Public visit and availability routes."""

from datetime import date

from flask import Blueprint, current_app, redirect, render_template, request, url_for

from app.catalog.floor_overlay import FLOOR_OVERLAY_MARKERS
from app.models import Booking
from app.services.availability import build_day_unit_statuses
from app.services.clock import today_in_timezone
from app.services.date_window import build_seven_day_strip, clamp_date_to_window

public_bp = Blueprint("public", __name__)


def _parse_date(value: str | None, fallback: date) -> date | None:
    """Parse ``YYYY-MM-DD`` or return None on invalid input."""
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


@public_bp.get("/")
def index():
    """Landing route redirects straight to availability."""
    return redirect(url_for("public.availability"))


@public_bp.get("/availability")
def availability():
    """
    Show occupancy for a single day inside the rolling seven-day window.

    Out-of-range ``?date=`` values redirect to today.
    """
    tz_name: str = current_app.config["TIMEZONE"]
    today = today_in_timezone(tz_name)

    parsed = _parse_date(request.args.get("date"), today)
    selected = parsed if parsed is not None else today
    if parsed is not None and clamp_date_to_window(parsed, today) != parsed:
        return redirect(url_for("public.availability", date=today.isoformat()))

    selected = clamp_date_to_window(selected, today)
    chips = build_seven_day_strip(today)
    bookings = Booking.query.all()
    unit_statuses = build_day_unit_statuses(selected, bookings)
    status_by_id = {status.unit_id: status for status in unit_statuses}

    return render_template(
        "public/availability.html",
        chips=chips,
        selected_date=selected,
        unit_statuses=unit_statuses,
        overlay_markers=FLOOR_OVERLAY_MARKERS,
        status_by_id=status_by_id,
    )
