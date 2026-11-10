"""WTForms for admin authentication and bookings."""

from datetime import datetime

from flask_wtf import FlaskForm
from wtforms import (
    DateField,
    IntegerField,
    PasswordField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import DataRequired, Length, NumberRange, Optional

from app.catalog import get_place_type, get_unit
from app.catalog.data import UNITS as ALL_UNITS
from app.catalog.types import Granularity
from app.models import BookingStatus
from app.services.booking_validation import (
    build_interval_daily,
    build_interval_hourly,
    build_interval_monthly,
)


class LoginForm(FlaskForm):
    """Administrator login."""

    username = StringField("Логин", validators=[DataRequired(), Length(max=64)])
    password = PasswordField("Пароль", validators=[DataRequired(), Length(max=128)])
    submit = SubmitField("Войти")


def _unit_choices() -> list[tuple[str, str]]:
    """Grouped labels for the unit select field."""
    choices: list[tuple[str, str]] = []
    for unit in ALL_UNITS:
        if not unit.active:
            continue
        place_type = get_place_type(unit.type_id)
        label = f"{place_type.title} — {unit.display_name}"
        choices.append((unit.id, label))
    return choices


class BookingForm(FlaskForm):
    """
    Unified booking form; time fields depend on the selected unit's granularity.

    The view layer shows or hides fields; the server always validates via
    ``resolve_interval``.
    """

    unit_id = SelectField("Место", choices=[], validators=[DataRequired()])
    status = SelectField(
        "Статус",
        choices=[
            (BookingStatus.PENDING.value, "Ожидает"),
            (BookingStatus.CONFIRMED.value, "Подтверждена"),
            (BookingStatus.CANCELLED.value, "Отменена"),
        ],
        default=BookingStatus.PENDING.value,
    )
    note = TextAreaField("Заметка", validators=[Optional(), Length(max=2000)])

    hourly_date = DateField("Дата (почасово)", validators=[Optional()])
    start_hour = IntegerField(
        "Час начала",
        validators=[Optional(), NumberRange(min=0, max=23)],
        default=9,
    )
    duration_hours = IntegerField(
        "Длительность (часы)",
        validators=[Optional(), NumberRange(min=1, max=24)],
        default=1,
    )

    daily_start = DateField("Дата начала (день)", validators=[Optional()])
    daily_end = DateField("Дата окончания (день)", validators=[Optional()])

    monthly_year = IntegerField("Год (месяц)", validators=[Optional()])
    monthly_month = IntegerField("Месяц", validators=[Optional(), NumberRange(min=1, max=12)])

    submit = SubmitField("Сохранить")

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.unit_id.choices = _unit_choices()

    def resolve_interval(
        self,
    ) -> tuple[datetime | None, datetime | None, str | None]:
        """
        Parse form data into booking bounds.

        Returns:
            (starts_at, ends_at, error_message)
        """
        try:
            unit = get_unit(self.unit_id.data)
            place_type = get_place_type(unit.type_id)
        except KeyError:
            return None, None, "Неизвестная единица."

        if place_type.granularity == Granularity.HOURLY:
            if not self.hourly_date.data:
                return None, None, "Укажите дату."
            built = build_interval_hourly(
                self.hourly_date.data,
                int(self.start_hour.data or 9),
                int(self.duration_hours.data or 1),
                place_type.hour_start,
                place_type.hour_end,
            )
            if built is None:
                return None, None, "Некорректный почасовой интервал."
            return built[0], built[1], None

        elif place_type.granularity == Granularity.DAILY:
            if not self.daily_start.data or not self.daily_end.data:
                return None, None, "Укажите даты начала и окончания."
            built = build_interval_daily(self.daily_start.data, self.daily_end.data)
            if built is None:
                return None, None, "Дата окончания раньше даты начала."
            return built[0], built[1], None

        elif place_type.granularity == Granularity.MONTHLY:
            if not self.monthly_year.data or not self.monthly_month.data:
                return None, None, "Укажите год и месяц."
            start, end = build_interval_monthly(
                int(self.monthly_year.data),
                int(self.monthly_month.data),
            )
            return start, end, None

        return None, None, "Неизвестный тип места."
