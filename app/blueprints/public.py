"""Public visit and availability routes."""

from datetime import date

from flask import Blueprint, current_app, redirect, render_template, request, url_for

from app.models import Booking
from app.services.availability import build_day_availability
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
def index() -> str:
    """Landing page with contact call-to-action."""
    return render_template("public/index.html")


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
    type_views = build_day_availability(selected, bookings)

    return render_template(
        "public/availability.html",
        chips=chips,
        selected_date=selected,
        type_views=type_views,
    )
