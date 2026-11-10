# Coworking Flask Site Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Реализовать v1 сайта-визитки коворкинга: публичная занятость по выбранному дню (полоса 7 дат) и админка броней на Flask + SQLite.

**Architecture:** Монолит с application factory; каталог типов/единиц в коде; единственная таблица `booking` с интервалами `[starts_at, ends_at)`; доменная логика в `services/`; blueprints `public` и `admin`.

**Tech Stack:** Python 3.11+, Flask, Flask-SQLAlchemy, Flask-Migrate, Flask-WTF, python-dotenv, pytest, zoneinfo.

**Spec:** [`docs/superpowers/specs/2026-11-10-coworking-flask-design.md`](../specs/2026-11-10-coworking-flask-design.md)

## Global Constraints

- TZ: `Europe/Moscow` (config `TIMEZONE`)
- Публичная занятость: только `BookingStatus.CONFIRMED`
- Пересечения: запрещены для одного `unit_id`, если `status != cancelled`
- Каталог: без таблиц в БД; типы/единицы только в `app/catalog/`
- Переговорная: почасовая сетка **09:00–21:00** в config типа
- `/availability?date=` вне [сегодня … сегодня+6] → redirect на сегодня
- Секреты: `FLASK_SECRET_KEY`, `ADMIN_USERNAME`, `ADMIN_PASSWORD` из env; не коммитить `.env`
- v1 без htmx, REST API, CRUD каталога в UI

## File map (итоговое дерево)

| Путь | Ответственность |
|------|-----------------|
| `requirements.txt` | Зависимости с пинами minor |
| `.env.example` | Шаблон env |
| `wsgi.py` | `app = create_app()` для PA/HelioHost |
| `app/__init__.py` | `create_app`, регистрация blueprints |
| `app/config.py` | `BaseConfig`, `TestingConfig` |
| `app/extensions.py` | `db`, `migrate`, `csrf` |
| `app/models.py` | `Booking`, `BookingStatus` enum |
| `app/catalog/types.py` | dataclass `PlaceType`, `Unit`, `Granularity` |
| `app/catalog/data.py` | v1 seed: переговорные, столы daily/monthly |
| `app/catalog/__init__.py` | `get_catalog()`, lookup helpers |
| `app/services/time_range.py` | overlap, align day/month boundaries |
| `app/services/date_window.py` | 7-day strip labels |
| `app/services/booking_validation.py` | validate + conflict query |
| `app/services/availability.py` | day view DTO для шаблона |
| `app/blueprints/public.py` | `/`, `/availability` |
| `app/blueprints/admin.py` | login, bookings CRUD |
| `app/blueprints/forms.py` | WTForms |
| `app/templates/**` | Jinja2 + Bootstrap 5 CDN |
| `app/static/css/main.css` | scroll-snap для полосы дат |
| `tests/conftest.py` | app, db, sample bookings |
| `tests/test_booking_validation.py` | |
| `tests/test_availability.py` | |
| `tests/test_public_routes.py` | |
| `migrations/` | Alembic initial |
| `README.md` | локальный запуск + PA/HelioHost |

---

### Task 1: Scaffold и конфигурация

**Files:**
- Create: `requirements.txt`, `.env.example`, `wsgi.py`, `app/__init__.py`, `app/config.py`, `app/extensions.py`
- Modify: `README.md`

**Interfaces:**
- Produces: `create_app(config_name: str | None = None) -> Flask`

- [ ] **Step 1: Зависимости**

`requirements.txt`:

```
Flask>=3.0,<4
Flask-SQLAlchemy>=3.1,<4
Flask-Migrate>=4.0,<5
Flask-WTF>=1.2,<2
python-dotenv>=1.0,<2
pytest>=8.0,<9
```

- [ ] **Step 2: `.env.example`**

```
FLASK_SECRET_KEY=change-me
ADMIN_USERNAME=admin
ADMIN_PASSWORD=change-me
DATABASE_URL=sqlite:///instance/coworking.db
TIMEZONE=Europe/Moscow
```

- [ ] **Step 3: `app/extensions.py`**

```python
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect

db = SQLAlchemy()
migrate = Migrate()
csrf = CSRFProtect()
```

- [ ] **Step 4: `app/config.py`**

```python
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


class BaseConfig:
    SECRET_KEY = os.environ["FLASK_SECRET_KEY"]
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", f"sqlite:///{BASE_DIR / 'instance' / 'coworking.db'}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TIMEZONE = os.getenv("TIMEZONE", "Europe/Moscow")
    ADMIN_USERNAME = os.environ["ADMIN_USERNAME"]
    ADMIN_PASSWORD = os.environ["ADMIN_PASSWORD"]
    WTF_CSRF_ENABLED = True


class TestingConfig(BaseConfig):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    WTF_CSRF_ENABLED = False
```

- [ ] **Step 5: `app/__init__.py`**

```python
from flask import Flask

from app.config import BaseConfig, TestingConfig
from app.extensions import csrf, db, migrate


def create_app(config_name: str | None = None) -> Flask:
    app = Flask(__name__, instance_relative_config=True)
    if config_name == "testing":
        app.config.from_object(TestingConfig)
    else:
        app.config.from_object(BaseConfig)

    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

  # blueprints register in later tasks

    return app
```

- [ ] **Step 6: `wsgi.py`**

```python
from dotenv import load_dotenv

load_dotenv()

from app import create_app

app = create_app()
```

- [ ] **Step 7: Проверка**

```bash
python -c "from dotenv import load_dotenv; load_dotenv('.env.example')"  # or real .env
pip install -r requirements.txt
```

- [ ] **Step 8: Commit** (по запросу пользователя)

```bash
git add requirements.txt .env.example wsgi.py app/
git commit -m "chore: Flask project scaffold"
```

---

### Task 2: Каталог типов и единиц

**Files:**
- Create: `app/catalog/types.py`, `app/catalog/data.py`, `app/catalog/__init__.py`
- Test: `tests/test_catalog.py`

**Interfaces:**
- Produces: `get_place_type(type_id: str) -> PlaceType`, `get_unit(unit_id: str) -> Unit`, `iter_active_units() -> list[Unit]`, `list_place_types() -> list[PlaceType]`

- [ ] **Step 1: Failing test**

```python
# tests/test_catalog.py
from app.catalog import get_unit, list_place_types


def test_catalog_has_meeting_room_type():
    types = list_place_types()
    ids = {t.id for t in types}
    assert "meeting_room" in ids, "expected meeting_room type in seed catalog"


def test_unit_links_to_type():
    unit = get_unit("room-a")
    assert unit.type_id == "meeting_room"
    assert unit.active is True
```

- [ ] **Step 2: Run**

```bash
pytest tests/test_catalog.py -v
```

Expected: FAIL (import errors)

- [ ] **Step 3: `app/catalog/types.py`**

```python
from dataclasses import dataclass
from enum import Enum


class Granularity(str, Enum):
    HOURLY = "hourly"
    DAILY = "daily"
    MONTHLY = "monthly"


@dataclass(frozen=True)
class PlaceType:
    id: str
    title: str
    granularity: Granularity
    hour_start: int = 9
    hour_end: int = 21  # exclusive end hour for slot generation


@dataclass(frozen=True)
class Unit:
    id: str
    type_id: str
    display_name: str
    active: bool = True
```

- [ ] **Step 4: `app/catalog/data.py`** (минимальный v1 seed)

```python
from app.catalog.types import Granularity, PlaceType, Unit

PLACE_TYPES: tuple[PlaceType, ...] = (
    PlaceType(
        id="meeting_room",
        title="Переговорные",
        granularity=Granularity.HOURLY,
        hour_start=9,
        hour_end=21,
    ),
    PlaceType(
        id="hot_desk",
        title="Столы (день)",
        granularity=Granularity.DAILY,
    ),
    PlaceType(
        id="dedicated_desk",
        title="Столы (месяц)",
        granularity=Granularity.MONTHLY,
    ),
)

UNITS: tuple[Unit, ...] = (
    Unit(id="room-a", type_id="meeting_room", display_name="Переговорная A"),
    Unit(id="room-b", type_id="meeting_room", display_name="Переговорная B"),
    Unit(id="desk-1", type_id="hot_desk", display_name="Стол 1"),
    Unit(id="desk-2", type_id="hot_desk", display_name="Стол 2"),
    Unit(id="desk-month-1", type_id="dedicated_desk", display_name="Стол M1"),
)
```

- [ ] **Step 5: `app/catalog/__init__.py`**

```python
from app.catalog.data import PLACE_TYPES, UNITS
from app.catalog.types import PlaceType, Unit


def list_place_types() -> list[PlaceType]:
    return list(PLACE_TYPES)


def get_place_type(type_id: str) -> PlaceType:
    for pt in PLACE_TYPES:
        if pt.id == type_id:
            return pt
    raise KeyError(type_id)


def get_unit(unit_id: str) -> Unit:
    for u in UNITS:
        if u.id == unit_id:
            return u
    raise KeyError(unit_id)


def iter_active_units() -> list[Unit]:
    return [u for u in UNITS if u.active]
```

- [ ] **Step 6: pytest PASS**

```bash
pytest tests/test_catalog.py -v
```

- [ ] **Step 7: Commit** (по запросу)

---

### Task 3: Time helpers и окно 7 дней

**Files:**
- Create: `app/services/time_range.py`, `app/services/date_window.py`
- Test: `tests/test_date_window.py`, `tests/test_time_range.py`

**Interfaces:**
- Produces: `ranges_overlap(a_start, a_end, b_start, b_end) -> bool`
- Produces: `build_seven_day_strip(today: date, tz: ZoneInfo) -> list[DayChip]` где `DayChip` имеет `iso`, `day_number`, `month_short_ru`, `weekday_short_ru`, `is_active`

- [ ] **Step 1: Failing tests**

```python
# tests/test_time_range.py
from datetime import datetime

from app.services.time_range import ranges_overlap


def test_ranges_overlap_half_open():
    a_start = datetime(2026, 11, 10, 10, 0)
    a_end = datetime(2026, 11, 10, 12, 0)
    b_start = datetime(2026, 11, 10, 11, 0)
    b_end = datetime(2026, 11, 10, 13, 0)
    assert ranges_overlap(a_start, a_end, b_start, b_end) is True


def test_ranges_no_touch_at_boundary():
    a_start = datetime(2026, 11, 10, 10, 0)
    a_end = datetime(2026, 11, 10, 11, 0)
    b_start = datetime(2026, 11, 10, 11, 0)
    b_end = datetime(2026, 11, 10, 12, 0)
    assert ranges_overlap(a_start, a_end, b_start, b_end) is False
```

```python
# tests/test_date_window.py
from datetime import date

from app.services.date_window import build_seven_day_strip


def test_strip_has_seven_days_starting_today():
    chips = build_seven_day_strip(date(2026, 11, 10))
    assert len(chips) == 7
    assert chips[0].iso == "2026-11-10"
    assert chips[6].iso == "2026-11-16"
```

- [ ] **Step 2: Implement `time_range.py`**

```python
from datetime import date, datetime
from calendar import monthrange


def ranges_overlap(
    a_start: datetime, a_end: datetime, b_start: datetime, b_end: datetime
) -> bool:
    return a_start < b_end and b_start < a_end


def day_bounds(d: date) -> tuple[datetime, datetime]:
    start = datetime(d.year, d.month, d.day)
    end = datetime(d.year, d.month, d.day)  # caller adds timedelta(days=1) for end
    return start, end


def month_bounds(year: int, month: int) -> tuple[datetime, datetime]:
    start = datetime(year, month, 1)
    if month == 12:
        end = datetime(year + 1, 1, 1)
    else:
        end = datetime(year, month + 1, 1)
    return start, end
```

- [ ] **Step 3: Implement `date_window.py`**

```python
from dataclasses import dataclass
from datetime import date, timedelta

MONTHS_SHORT_RU = (
    "янв", "фев", "мар", "апр", "май", "июн",
    "июл", "авг", "сен", "окт", "ноя", "дек",
)
WEEKDAYS_SHORT_RU = ("пн", "вт", "ср", "чт", "пт", "сб", "вс")


@dataclass(frozen=True)
class DayChip:
    iso: str
    day_number: int
    month_short_ru: str
    weekday_short_ru: str


def build_seven_day_strip(anchor: date) -> list[DayChip]:
    chips: list[DayChip] = []
    for offset in range(7):
        d = anchor + timedelta(days=offset)
        chips.append(
            DayChip(
                iso=d.isoformat(),
                day_number=d.day,
                month_short_ru=MONTHS_SHORT_RU[d.month - 1],
                weekday_short_ru=WEEKDAYS_SHORT_RU[d.weekday()],
            )
        )
    return chips


def clamp_date_to_window(requested: date, today: date) -> date:
    last = today + timedelta(days=6)
    if requested < today or requested > last:
        return today
    return requested
```

- [ ] **Step 4: pytest PASS**

```bash
pytest tests/test_time_range.py tests/test_date_window.py -v
```

---

### Task 4: Модель Booking и миграция

**Files:**
- Create: `app/models.py`, `tests/conftest.py`
- Modify: `app/__init__.py` (import models for Alembic)

**Interfaces:**
- Produces: `class BookingStatus(str, Enum)`, `class Booking(db.Model)` с полями из spec

- [ ] **Step 1: `app/models.py`**

```python
import enum
from datetime import datetime

from app.extensions import db


class BookingStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"


class Booking(db.Model):
    __tablename__ = "booking"

    id = db.Column(db.Integer, primary_key=True)
    unit_id = db.Column(db.String(64), nullable=False, index=True)
    starts_at = db.Column(db.DateTime, nullable=False)
    ends_at = db.Column(db.DateTime, nullable=False)
    status = db.Column(
        db.Enum(BookingStatus, name="booking_status", native_enum=False),
        nullable=False,
        default=BookingStatus.PENDING,
    )
    note = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    __table_args__ = (
        db.Index("ix_booking_unit_interval", "unit_id", "starts_at", "ends_at"),
    )
```

- [ ] **Step 2: `tests/conftest.py`**

```python
import pytest

from app import create_app
from app.extensions import db


@pytest.fixture
def app():
    application = create_app("testing")
    with application.app_context():
        db.create_all()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()
```

- [ ] **Step 3: Миграция**

```bash
set FLASK_APP=wsgi.py
flask db init
flask db migrate -m "create booking table"
flask db upgrade
```

- [ ] **Step 4: Smoke test**

```python
# tests/test_models.py
from datetime import datetime

from app.extensions import db
from app.models import Booking, BookingStatus


def test_persist_booking(app):
    with app.app_context():
        b = Booking(
            unit_id="room-a",
            starts_at=datetime(2026, 11, 10, 10, 0),
            ends_at=datetime(2026, 11, 10, 12, 0),
            status=BookingStatus.CONFIRMED,
        )
        db.session.add(b)
        db.session.commit()
        assert b.id is not None
```

---

### Task 5: `booking_validation`

**Files:**
- Create: `app/services/booking_validation.py`
- Test: `tests/test_booking_validation.py`

**Interfaces:**
- Consumes: `get_unit`, `get_place_type`, `Booking` query
- Produces: `ValidationResult(ok: bool, errors: list[str])`, `find_conflicts(unit_id, start, end, exclude_id=None) -> list[Booking]`, `normalize_interval_for_type(unit_id, fields...) -> tuple[datetime, datetime]`

- [ ] **Step 1: Failing tests** (пересечение + inactive unit)

```python
from datetime import date, datetime

import pytest

from app.extensions import db
from app.models import Booking, BookingStatus
from app.services.booking_validation import assert_can_save_booking


@pytest.fixture
def room_booking(app):
    with app.app_context():
        b = Booking(
            unit_id="room-a",
            starts_at=datetime(2026, 11, 10, 10, 0),
            ends_at=datetime(2026, 11, 10, 12, 0),
            status=BookingStatus.PENDING,
        )
        db.session.add(b)
        db.session.commit()
        return b.id


def test_rejects_overlap_same_unit(app, room_booking):
    with app.app_context():
        result = assert_can_save_booking(
            unit_id="room-a",
            starts_at=datetime(2026, 11, 10, 11, 0),
            ends_at=datetime(2026, 11, 10, 13, 0),
            status=BookingStatus.CONFIRMED,
        )
        assert result.ok is False
        assert any("пересеч" in e.lower() for e in result.errors)


def test_cancelled_does_not_block(app, room_booking):
    with app.app_context():
        old = db.session.get(Booking, room_booking)
        old.status = BookingStatus.CANCELLED
        db.session.commit()
        result = assert_can_save_booking(
            unit_id="room-a",
            starts_at=datetime(2026, 11, 10, 11, 0),
            ends_at=datetime(2026, 11, 10, 13, 0),
            status=BookingStatus.CONFIRMED,
        )
        assert result.ok is True
```

- [ ] **Step 2: Implement** `assert_can_save_booking` с запросом:

```python
Booking.query.filter(
    Booking.unit_id == unit_id,
    Booking.status != BookingStatus.CANCELLED,
    Booking.starts_at < ends_at,
    Booking.ends_at > starts_at,
)
```

+ проверка `unit.active` + выравнивание hourly (целые часы в 9–21), daily (полные дни), monthly (`month_bounds`).

- [ ] **Step 3: pytest PASS**

```bash
pytest tests/test_booking_validation.py -v
```

---

### Task 6: `availability` для одного дня

**Files:**
- Create: `app/services/availability.py`
- Test: `tests/test_availability.py`

**Interfaces:**
- Produces: `build_day_availability(selected: date, bookings: list[Booking]) -> list[TypeDayView]`
- `TypeDayView`: `type_id`, `title`, `rows` (почасовые слоты или daily/monthly строки), `free_count`, `occupied_names`

- [ ] **Step 1: Failing test** — only confirmed counts

```python
from datetime import date, datetime

from app.extensions import db
from app.models import Booking, BookingStatus
from app.services.availability import build_day_availability


def test_pending_not_shown_as_occupied(app):
    with app.app_context():
        db.session.add(
            Booking(
                unit_id="room-a",
                starts_at=datetime(2026, 11, 10, 10, 0),
                ends_at=datetime(2026, 11, 10, 11, 0),
                status=BookingStatus.PENDING,
            )
        )
        db.session.commit()
        views = build_day_availability(date(2026, 11, 10))
        meeting = next(v for v in views if v.type_id == "meeting_room")
        slot_10 = next(r for r in meeting.rows if r.label == "10:00–11:00")
        assert "Переговорная A" not in slot_occupied_names(slot_10)
```

(в тесте добавить маленький helper `slot_occupied_names` или проверять `occupied_unit_names` на dataclass `SlotRow`.)

- [ ] **Step 2: Implement**

- Загрузить confirmed bookings, пересекающие выбранный день.
- Для `hourly`: сгенерировать слоты `f"{h:02d}:00–{h+1:02d}:00"` от `hour_start` до `hour_end-1`.
- Для `daily`: одна строка «Весь день», unit занят если бронь пересекает day bounds.
- Для `monthly`: аналогично пересечению дня с месячной бронью.

- [ ] **Step 3: pytest PASS**

```bash
pytest tests/test_availability.py -v
```

---

### Task 7: Public blueprint и шаблоны

**Files:**
- Create: `app/blueprints/public.py`, `templates/base.html`, `templates/public/index.html`, `templates/public/availability.html`, `app/static/css/main.css`
- Modify: `app/__init__.py` register blueprint

**Interfaces:**
- Consumes: `build_seven_day_strip`, `clamp_date_to_window`, `build_day_availability`

- [ ] **Step 1: Integration test**

```python
def test_availability_redirects_out_of_window(client):
    # mock 'today' via freezegun optional; or set date far in future in query
    resp = client.get("/availability?date=2099-01-01", follow_redirects=False)
    assert resp.status_code == 302
    assert "date=" in resp.headers["Location"]


def test_availability_ok(client):
    resp = client.get("/availability")
    assert resp.status_code == 200
    assert b"Переговорные" in resp.data
```

- [ ] **Step 2: `public.py`**

- `index()` → render `public/index.html`
- `availability()`:
  - `today = date.today()` (позже inject TZ-aware `today_moscow()` helper)
  - parse `request.args.get("date")`, redirect if out of window
  - query confirmed+p вс bookings overlapping day (availability service filters)
  - render with `chips`, `selected_date`, `type_views`

- [ ] **Step 3: Templates**

- `availability.html`: полоса 7 `<a class="day-chip">` со столбиком число/месяц/ДН; таблицы по типам
- CSS: `.day-strip { display:flex; overflow-x:auto; scroll-snap-type:x mandatory; }`

- [ ] **Step 4: pytest**

```bash
pytest tests/test_public_routes.py -v
```

---

### Task 8: Admin auth и CRUD броней

**Files:**
- Create: `app/blueprints/admin.py`, `app/blueprints/forms.py`, templates `admin/login.html`, `admin/bookings_list.html`, `admin/booking_form.html`
- Modify: `app/__init__.py`

**Interfaces:**
- Consumes: `assert_can_save_booking`, catalog для grouped unit select

- [ ] **Step 1: Test login**

```python
def test_admin_login_requires_password(client, app):
    resp = client.post("/admin/login", data={"username": "x", "password": "y"})
    assert resp.status_code == 200
    assert b"Невер" in resp.data or resp.status_code == 401


def test_admin_bookings_redirect_anonymous(client):
    resp = client.get("/admin/bookings", follow_redirects=False)
    assert resp.status_code in (302, 401)
```

- [ ] **Step 2: Session guard**

```python
def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("admin.login"))
        return view(*args, **kwargs)
    return wrapped
```

- [ ] **Step 3: Forms**

- `LoginForm`, `BookingForm` с динамическими подполями по granularity (скрытые WTForms или отдельные Optional поля + server parse)

- [ ] **Step 4: Routes** list/create/edit per spec

- [ ] **Step 5: Manual smoke**

```bash
flask --app wsgi run
# login, create confirmed booking, check /availability
```

---

### Task 9: README и деплой

**Files:**
- Modify: `README.md`

- [ ] Локально: venv, `.env`, `flask db upgrade`, `flask run`
- [ ] PythonAnywhere: upload, virtualenv, WSGI `wsgi.py`, static mapping
- [ ] HelioHost: аналогично + путь к SQLite в `instance/` с правами записи
- [ ] Не коммитить секреты

---

### Task 10: Финальная верификация

- [ ] **Run full suite**

```bash
pytest -v
```

- [ ] **Lint** (optional): `ruff check app tests` if ruff added later

- [ ] **Spec walkthrough:** чеклист по spec section → task mapping (см. ниже)

---

## Plan self-review

### Spec coverage

| Spec section | Task |
|--------------|------|
| Архитектура / env | 1 |
| Каталог | 2 |
| 7-day UI + clamp | 3, 7 |
| Booking model | 4 |
| Пересечения / validation | 5 |
| Публичная логика confirmed | 6, 7 |
| Админка | 8 |
| pytest | 5, 6, 7, 10 |
| Деплой README | 9 |

### Placeholder scan

Нет TBD/TODO в задачах; граничные сообщения об ошибках реализуются в Task 5/8 при кодировании форм.

### Type consistency

`BookingStatus`, `DayChip`, `assert_can_save_booking`, `build_day_availability` — единые имена во всех задачах.

---

## Порядок для исполнителя

Строго: **1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10**. Не начинать Task 7 до прохождения тестов Task 6.
