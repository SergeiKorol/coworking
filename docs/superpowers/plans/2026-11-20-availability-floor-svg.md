# Availability Floor SVG Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Заменить PNG + CSS-текстовые оверлеи на странице `/availability` полноценный inline-SVG с подсветкой столов 1–8 и стола переговорки (белый = свободно, фуксия = занято), сохранив карточки под схемой.

**Architecture:** Jinja-partial `floor_plan.svg` встраивается в `availability.html`; классы `floor-unit--free|busy` на `<g data-unit-id>` выставляются из `status_by_id`; статичная векторная графика и управляемые группы в одном `viewBox`. Python не хранит координаты — только каталог и `build_day_unit_statuses`.

**Tech Stack:** Flask, Jinja2, SVG, CSS (`availability-v2.css`), pytest + Flask test client.

**Spec:** [`docs/superpowers/specs/2026-11-20-availability-floor-svg-design.md`](../specs/2026-11-20-availability-floor-svg-design.md)

## Global Constraints

- Статус на плане: **без** текста «свободен/занят»; только цвет
- Стол: кружок `#ffffff` / `#d946ef`; цифра `#1a1a1a` / `#ffffff`; обводка круга `rgba(0,0,0,0.25)` в свободном состоянии
- Переговорка: заливка стола `#ffffff` / `#d946ef`
- Карточки `unit-card` под схемой **остаются**
- Каталог: `desk-1`…`desk-8`, `meeting-room` — **9** групп в SVG
- Занятость: только `BookingStatus.CONFIRMED` (без изменений сервиса)
- Нет `floor-overlay-marker` в HTML ответа
- PNG плана **не** подключать в `availability.html` (файл можно оставить в `static/images/` как референс)

## File map

| Путь | Действие |
|------|----------|
| `tests/test_floor_plan_svg.py` | Create — markup/class tests |
| `app/templates/public/availability.html` | Modify — include SVG |
| `app/templates/public/floor_plan.svg` | Create — vector partial |
| `app/static/css/availability-v2.css` | Modify — unit classes, drop overlay |
| `app/blueprints/public.py` | Modify — убрать `overlay_markers` |
| `app/catalog/floor_overlay.py` | Delete (после удаления импортов) |
| `tests/test_public_routes.py` | Modify — опционально assert `floor-plan-svg` |
| `docs/superpowers/specs/2026-11-13-availability-ui-v2-design.md` | Modify — ссылка на новую спеку (одна строка) |

---

### Task 1: Markup tests (TDD)

**Files:**
- Create: `tests/test_floor_plan_svg.py`

**Interfaces:**
- Consumes: `client` fixture from `tests/conftest.py`, `flask_app`, `db` for booking seed

- [ ] **Step 1: Write tests**

```python
"""Public availability page — SVG floor plan markup."""

from datetime import datetime

from app.extensions import db
from app.models import Booking, BookingStatus


def test_availability_uses_svg_not_png_overlay(client) -> None:
    response = client.get("/availability")
    assert response.status_code == 200, "availability must render"
    body = response.data.decode("utf-8")
    assert "floor-plan-svg" in body, "page must embed SVG floor plan"
    assert "floor-overlay-marker" not in body, "legacy CSS overlays must be removed"
    assert 'floor-plan-img' not in body, "raster floor img must not be used"
    assert 'data-unit-id="desk-1"' in body, "desk groups must be addressable"
    assert 'data-unit-id="meeting-room"' in body, "meeting room group must exist"


def test_desk_free_by_default_has_free_class(client) -> None:
    response = client.get("/availability")
    body = response.data.decode("utf-8")
    assert 'data-unit-id="desk-1"' in body
    idx = body.index('data-unit-id="desk-1"')
    snippet = body[max(0, idx - 120) : idx + 120]
    assert "floor-unit--free" in snippet, "unbooked desk must be free on the plan"


def test_confirmed_desk_shows_busy_class(client, flask_app) -> None:
    with flask_app.app_context():
        db.session.add(
            Booking(
                unit_id="desk-2",
                starts_at=datetime(2026, 11, 10),
                ends_at=datetime(2026, 11, 11),
                status=BookingStatus.CONFIRMED,
            )
        )
        db.session.commit()
    response = client.get("/availability?date=2026-11-10")
    body = response.data.decode("utf-8")
    idx = body.index('data-unit-id="desk-2"')
    snippet = body[max(0, idx - 120) : idx + 120]
    assert "floor-unit--busy" in snippet, "confirmed booking must mark desk busy on SVG"


def test_cards_still_present(client) -> None:
    response = client.get("/availability")
    body = response.data.decode("utf-8")
    assert "unit-card" in body, "unit cards must remain under the plan"
    assert "Стол 1" in body, "card titles must still list desks"
```

- [ ] **Step 2: Run tests (expect FAIL)**

```bash
pytest tests/test_floor_plan_svg.py -v
```

Expected: FAIL — `floor-plan-svg` missing, `floor-overlay-marker` still present.

- [ ] **Step 3: Commit**

```bash
git add tests/test_floor_plan_svg.py
git commit -m "test: availability SVG floor plan markup"
```

---

### Task 2: Blueprint and availability template shell

**Files:**
- Modify: `app/blueprints/public.py`
- Modify: `app/templates/public/availability.html`

**Interfaces:**
- Consumes: `status_by_id`, `unit_statuses`, `chips`, `selected_date` (unchanged)
- Produces: include `public/floor_plan.svg` with `status_by_id` in context (already passed)

- [ ] **Step 1: Remove overlay import and template kwarg**

`app/blueprints/public.py` — delete line:

```python
from app.catalog.floor_overlay import FLOOR_OVERLAY_MARKERS
```

and remove `overlay_markers=FLOOR_OVERLAY_MARKERS,` from `render_template(...)`.

- [ ] **Step 2: Replace floor block in `availability.html`**

Replace the `div.floor-plan-wrap` content (img + overlay loop) with:

```jinja
<div class="floor-plan-wrap">
  {% include "public/floor_plan.svg" %}
</div>
```

- [ ] **Step 3: Run tests**

```bash
pytest tests/test_floor_plan_svg.py -v
```

Expected: still FAIL until `floor_plan.svg` exists (Jinja `TemplateNotFound` or missing classes).

- [ ] **Step 4: Commit**

```bash
git add app/blueprints/public.py app/templates/public/availability.html
git commit -m "refactor: wire SVG partial hook on availability page"
```

---

### Task 3: CSS for floor units

**Files:**
- Modify: `app/static/css/availability-v2.css`

**Interfaces:**
- Produces: selectors `.floor-plan-svg`, `.floor-unit--free`, `.floor-unit--busy`

- [ ] **Step 1: Add SVG + unit rules; remove overlay marker block**

After `.floor-plan-wrap { ... }`, replace `.floor-plan-img` and entire `.floor-overlay-marker*` section with:

```css
.floor-plan-svg {
  display: block;
  width: 100%;
  height: auto;
}

.floor-unit--free .floor-unit__badge {
  fill: #ffffff;
  stroke: rgba(0, 0, 0, 0.25);
  stroke-width: 1.5;
}

.floor-unit--free .floor-unit__label {
  fill: #1a1a1a;
}

.floor-unit--busy .floor-unit__badge {
  fill: #d946ef;
  stroke: rgba(0, 0, 0, 0.15);
  stroke-width: 1.5;
}

.floor-unit--busy .floor-unit__label {
  fill: #ffffff;
}

.floor-unit--free .floor-unit__table {
  fill: #ffffff;
}

.floor-unit--busy .floor-unit__table {
  fill: #d946ef;
}
```

Remove mobile `.floor-overlay-marker` rule inside `@media (max-width: 768px)`.

- [ ] **Step 2: Commit**

```bash
git add app/static/css/availability-v2.css
git commit -m "style: SVG floor unit free/busy colors"
```

---

### Task 4: Vector partial `floor_plan.svg`

**Files:**
- Create: `app/templates/public/floor_plan.svg`

**Interfaces:**
- Consumes: `status_by_id`, `selected_date` from parent template context
- Produces: root `<svg class="floor-plan-svg">` with 9 status groups

**Notes for implementer:** Trace `app/static/images/floor_plan.png` in Inkscape/Figma. Target `viewBox="0 0 1200 800"` (adjust after trace). Keep decorative layers in `<g id="floor-decor" aria-hidden="true">`. Each status group sets class from Jinja.

- [ ] **Step 1: Create partial skeleton (passes tests; refine art in Step 2)**

Create `app/templates/public/floor_plan.svg` with structure below — **replace decorative paths** when tracing; keep `data-unit-id`, class pattern, and `floor-unit__*` class names on shapes.

```jinja
<svg
  class="floor-plan-svg"
  xmlns="http://www.w3.org/2000/svg"
  viewBox="0 0 1200 800"
  role="img"
  aria-labelledby="floor-plan-title"
>
  <title id="floor-plan-title">Схема коворкинга, занятость на {{ selected_date.strftime('%d.%m.%Y') }}</title>

  <g id="floor-decor" aria-hidden="true">
    <rect x="0" y="0" width="1200" height="800" fill="#2b2f33"/>
    <!-- TODO trace: room outlines, labels ПЕРЕГОВОРКА / ОСНОВНОЙ ЗАЛ, desk shapes without numbers -->
  </g>

  <g
    id="meeting-room"
    data-unit-id="meeting-room"
    class="floor-unit {% if status_by_id['meeting-room'].occupied %}floor-unit--busy{% else %}floor-unit--free{% endif %}"
    aria-label="{{ status_by_id['meeting-room'].display_name }}, {% if status_by_id['meeting-room'].occupied %}занята{% else %}свободна{% endif %}"
  >
    <rect class="floor-unit__table" x="80" y="200" width="320" height="120" rx="12"/>
  </g>

  {% for n in range(1, 9) %}
  {% set uid = 'desk-' ~ n %}
  {% set st = status_by_id[uid] %}
  <g
    id="{{ uid }}"
    data-unit-id="{{ uid }}"
    class="floor-unit {% if st.occupied %}floor-unit--busy{% else %}floor-unit--free{% endif %}"
    aria-label="{{ st.display_name }}, {% if st.occupied %}занят{% else %}свободен{% endif %}"
  >
    <circle class="floor-unit__badge" cx="{{ 480 + (n % 4) * 140 }}" cy="{{ 280 + (n // 4) * 200 }}" r="22"/>
    <text class="floor-unit__label" x="{{ 480 + (n % 4) * 140 }}" y="{{ 280 + (n // 4) * 200 }}" text-anchor="middle" dominant-baseline="central" font-size="20" font-weight="600">{{ n }}</text>
  </g>
  {% endfor %}
</svg>
```

**Step 1 coordinates are placeholders** — Step 2 aligns `cx/cy` and decor paths to the real mock.

- [ ] **Step 2: Visual trace pass**

1. Open `floor_plan.png` beside browser at `/availability`.
2. Move each desk circle center to match mock numbers 1–8.
3. Replace meeting `rect` with traced `path` for table shape.
4. Add decor paths (walls, chairs as static fills) — no raster `<image>`.

- [ ] **Step 3: Run full test suite**

```bash
pytest -v
```

Expected: all tests PASS including `test_floor_plan_svg.py`.

- [ ] **Step 4: Commit**

```bash
git add app/templates/public/floor_plan.svg
git commit -m "feat: vector floor plan with status highlighting"
```

---

### Task 5: Remove legacy overlay module

**Files:**
- Delete: `app/catalog/floor_overlay.py`
- Modify: repo-wide grep for `floor_overlay` / `FLOOR_OVERLAY`

**Interfaces:**
- Produces: no Python overlay coordinates

- [ ] **Step 1: Grep and delete**

```bash
rg "floor_overlay|FLOOR_OVERLAY" .
```

Remove file and any remaining references (should be none after Task 2).

- [ ] **Step 2: Run tests**

```bash
pytest -v
```

- [ ] **Step 3: Commit**

```bash
git add -A
git commit -m "chore: remove CSS floor overlay markers module"
```

---

### Task 6: Docs and spec cross-link

**Files:**
- Modify: `docs/superpowers/specs/2026-11-13-availability-ui-v2-design.md` (таблица «Принятые решения», строка Схема)
- Modify: `docs/superpowers/specs/2026-11-20-availability-floor-svg-design.md` — статус: «утверждён»

- [ ] **Step 1: Update v2 spec row**

Change scheme row to: `SVG inline (см. 2026-11-20-availability-floor-svg-design.md)`.

- [ ] **Step 2: Mark SVG spec approved**

`- **Статус:** утверждён пользователем`

- [ ] **Step 3: Commit**

```bash
git add docs/superpowers/specs/
git commit -m "docs: approve floor SVG spec and cross-link v2"
```

---

## Spec coverage self-review

| Spec requirement | Task |
|------------------|------|
| Full vector SVG, no PNG in page | 2, 4 |
| Remove text overlays | 2, 3, 5 |
| Desk circle + digit colors | 3, 4 |
| Meeting table fill | 3, 4 |
| Keep cards | 1 (test), unchanged template section |
| aria-label on groups | 4 |
| Tests for classes / no legacy markup | 1 |
| Remove `floor_overlay.py` | 5 |
| 8 desks + meeting room | 4 loop `range(1, 9)` |

## Placeholder scan

- Desk coordinates in Task 4 Step 1 are explicitly labeled placeholders with Step 2 trace — acceptable workflow step, not a skipped requirement.
- No TBD in committed code paths.

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-11-20-availability-floor-svg.md`.

**Two execution options:**

1. **Subagent-Driven (recommended)** — fresh subagent per task, review between tasks  
2. **Inline Execution** — implement tasks in this session with checkpoints

Which approach do you prefer?