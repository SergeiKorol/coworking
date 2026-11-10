"""Seven-day date strip for the public availability page."""

from dataclasses import dataclass
from datetime import date, timedelta

MONTHS_SHORT_RU: tuple[str, ...] = (
    "янв",
    "фев",
    "мар",
    "апр",
    "май",
    "июн",
    "июл",
    "авг",
    "сен",
    "окт",
    "ноя",
    "дек",
)
WEEKDAYS_SHORT_RU: tuple[str, ...] = ("пн", "вт", "ср", "чт", "пт", "сб", "вс")


@dataclass(frozen=True)
class DayChip:
    """Label data for one button in the seven-day strip."""

    iso: str
    day_number: int
    month_short_ru: str
    weekday_short_ru: str


def build_seven_day_strip(anchor: date) -> list[DayChip]:
    """
    Build seven consecutive days beginning at ``anchor`` (usually today).

    The leftmost chip is ``anchor``; the rightmost is ``anchor + 6 days``.
    """
    chips: list[DayChip] = []
    for offset in range(7):
        current = anchor + timedelta(days=offset)
        chips.append(
            DayChip(
                iso=current.isoformat(),
                day_number=current.day,
                month_short_ru=MONTHS_SHORT_RU[current.month - 1],
                weekday_short_ru=WEEKDAYS_SHORT_RU[current.weekday()],
            )
        )
    return chips


def clamp_date_to_window(requested: date, today: date) -> date:
    """
  Return ``requested`` when it falls in ``[today, today + 6]``; otherwise ``today``.
    """
    last_allowed = today + timedelta(days=6)
    if requested < today or requested > last_allowed:
        return today
    return requested
