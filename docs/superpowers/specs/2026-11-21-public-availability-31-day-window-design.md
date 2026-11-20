# Дизайн: публичное окно занятости 31 день

**Дата:** 2026-11-21  
**Статус:** частично устарела (горизонт +30 актуален; UI заменён — [2026-11-21-availability-strip-calendar-design.md](./2026-11-21-availability-strip-calendar-design.md))  
**Родительский scope:** [2026-11-10-coworking-flask-design.md](./2026-11-10-coworking-flask-design.md), [2026-11-13-availability-ui-v2-design.md](./2026-11-13-availability-ui-v2-design.md)

## Цель

Расширить публичную страницу `/availability`: посетитель видит занятость на **любой день** в диапазоне **сегодня … сегодня + 30** (31 календарный день), сохраняя показ **одного дня** на экране (схема + карточки). Навигация: **7 чипов**, сдвигаемая вокруг выбранной даты, **стрелки ±7 дней**, нативный **date picker**.

## Вне scope

- Занятость сразу на несколько дней / месячный heatmap.
- Бронирование с сайта, API.
- Изменение горизонта в админке или в БД.
- Кастомный календарный виджет (только `input type="date"`).
- Просмотр дат **до today**.

## Принятые решения (брейншторм)

| Тема | Решение |
|------|---------|
| Горизонт | **today … today + 30** (скользящее окно +30) |
| Прошлое | Запрещено; out-of-range → redirect на `?date=today` |
| Полоса чипов | **7 дней**, окно **центрируется** вокруг `selected` (края — прижатие к today / last) |
| Дальние даты | **C:** стрелки ±7 дней + «Другая дата» (`input type="date"`) |
| Контент дня | Схема PNG-in-SVG, карточки — **без изменений** |

## Поведение

### Маршрут `GET /availability?date=`

1. `today = today_in_timezone(TIMEZONE)`.
2. `last_allowed = today + timedelta(days=30)`.
3. Парсинг `date` query; если нет — `selected = today`.
4. Если `selected < today` или `selected > last_allowed` — **302** на `url_for('public.availability', date=today.isoformat())`.
5. Иначе `selected = clamp` (уже в диапазоне).
6. `chips = build_seven_day_strip_centered(selected, today, last_allowed)`.
7. Рендер с `selected_date`, `chips`, `min_date=today`, `max_date=last_allowed` (для date input).

### `build_seven_day_strip_centered`

Вход: `selected`, `today`, `last` (все `date`, `today <= selected <= last`).

Алгоритм (индексы в днях от `today`):

- `span = last - today` в днях (макс. 30).
- Желаемый старт полосы: `selected - 3` дня, но не раньше `today` и не позже так, чтобы конец полосы ≤ `last`.
- Реализация: `start = selected - timedelta(days=3)`; `if start < today: start = today`; `end = start + 6 days`; `if end > last: end = last; start = max(today, end - 6 days)`.
- Вернуть `DayChip` для каждого дня от `start` до `end` включительно (всегда **7** чипов, если `span >= 6`; если горизонт короче 7 дней — теоретически не бывает при +30).

Существующий `build_seven_day_strip(anchor)` можно оставить для обратной совместимости тестов или заменить использованием `centered` с `selected=today`.

### `clamp_date_to_window`

Заменить верхнюю границу с `+6` на `+30`:

```python
last_allowed = today + timedelta(days=30)
if requested < today or requested > last_allowed:
    return today
return requested
```

Константа модуля: `PUBLIC_AVAILABILITY_HORIZON_DAYS = 30`.

## UI

### Разметка (над `day-strip`)

```text
[ ← Пред. неделя ]  [ Другая дата ▼ ]  [ След. неделя → ]
```

- Ссылки стрелок: `/availability?date={{ (selected_date - 7d).isoformat() }}` с учётом clamp (шаблон не считает clamp — **ссылки генерирует view** или Jinja-фильтр; предпочтение: передать `prev_week_date`, `next_week_date` из view после clamp).
- `prev = max(today, selected - 7)`, `next = min(last, selected + 7)`.
- Кнопки **disabled** (не ссылка, класс `disabled`), если `prev == selected` или `next == selected` на краях — опционально; допустимы ссылки с той же датой (no-op).

### Date input

```html
<input type="date"
  id="availability-date-picker"
  name="date"
  min="{{ min_date.isoformat() }}"
  max="{{ max_date.isoformat() }}"
  value="{{ selected_date.isoformat() }}"
  aria-label="Выберите дату"
/>
```

Поведение: `change` event → `window.location.href = '/availability?date=' + value` (относительный путь через `url_for` в data-атрибуте). Минимальный inline-script в `availability.html` или в `main.js` — только этот обработчик.

Подпись кнопки: **«Другая дата»** (текст рядом с input или label for).

### Чипы

Без изменения структуры; `href` как сейчас; `day-chip--active` для `selected`.

### Стили

- Блок `.availability-date-nav`: flex, gap, центрирование на mobile.
- `input[type="date"]`: читаемая высота на touch targets.
- Стрелки: классы совместимые с Bootstrap (`btn btn-outline-secondary btn-sm`) если `base_public` уже тянет Bootstrap.

## Архитектура

| Компонент | Изменение |
|-----------|-----------|
| `app/services/date_window.py` | `HORIZON_DAYS`, `clamp`, `build_seven_day_strip_centered` |
| `app/blueprints/public.py` | Граница +30, centered strip, контекст min/max/prev/next |
| `app/templates/public/availability.html` | Навигация + date input + script |
| `app/static/css/main.css` или `availability-v2.css` | Стили навигации |

Конфиг env **не обязателен** в первой итерации.

## Тестирование

| Тест | Ожидание |
|------|----------|
| `clamp` / strip | Центрирование у `today`, у `last`, в середине |
| `GET ?date=last` | 200 |
| `GET ?date=last+1` | 302 на today |
| `GET ?date=yesterday` | 302 на today |
| HTML | `type="date"`, `min`/`max`, ссылки prev/next |

Обновить `tests/test_date_window.py`, `tests/test_public_routes.py`; при необходимости `tests/test_availability.py` без изменений логики occupied.

## Риски

| Риск | Смягчение |
|------|-----------|
| Date input в старых Safari | Деградация: остаются чипы и стрелки |
| `Booking.query.all()` на дальние даты | Без изменений; объём данных мал |

## Связь с v2 spec

В [2026-11-13-availability-ui-v2-design.md](./2026-11-13-availability-ui-v2-design.md) строка «окно 7 дней» считается **расширенной** данным документом (горизонт 31 день, полоса 7 чипов с центрированием).