"""Date strip and horizon for the public availability page."""

from dataclasses import dataclass
from datetime import date, timedelta

PUBLIC_AVAILABILITY_HORIZON_DAYS = 30

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


def last_allowed_date(today: date) -> date:
    """Last calendar day visitors may open on the public availability page."""
    return today + timedelta(days=PUBLIC_AVAILABILITY_HORIZON_DAYS)


def build_seven_day_strip(today: date) -> list[DayChip]:
    """
    Seven consecutive days from ``today`` (the rolling “this week” strip).
    """
    chips: list[DayChip] = []
    for offset in range(7):
        current = today + timedelta(days=offset)
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
    Return ``requested`` when it falls in ``[today, last_allowed]``; otherwise ``today``.
    """
    last_allowed = last_allowed_date(today)
    if requested < today or requested > last_allowed:
        return today
    return requested