"""Timezone-aware clock helpers."""

from datetime import date, datetime
from zoneinfo import ZoneInfo


def today_in_timezone(tz_name: str) -> date:
    """Return the current calendar date in the configured timezone."""
    return datetime.now(ZoneInfo(tz_name)).date()
