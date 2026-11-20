# Дизайн: схема занятости — PNG в SVG + подсветка hotspots

**Дата:** 2026-11-21  
**Статус:** утверждён пользователем  
**Родительский scope:** [2026-11-13-availability-ui-v2-design.md](./2026-11-13-availability-ui-v2-design.md)  
**Заменяет:** [2026-11-20-availability-floor-svg-design.md](./2026-11-20-availability-floor-svg-design.md) (полный векторный план — **отменён** из‑за расхождения с макетом)

## Цель

На `/availability` показывать **оригинальный растр** `floor_plan.png` (пиксель в пиксель с макетом) и поверх него — **только цветовую подсветку** мест: кружки с цифрами 1–8 и заливка стола переговорки. Текстовые бейджи «Стол N / свободен» на схеме **запрещены**. Карточки под планом **сохраняются**.

## Мотивация смены подхода

Полностью векторная схема (2026-11-20) визуально далека от PNG. Гибрид **B**: `<image>` + векторные hotspots в одном `viewBox` даёт совпадение с макетом на **desktop и mobile** при `width: 100%` (масштабирование без рассинхрона слоёв).

## Вне scope

- Логика `build_day_unit_statuses`, каталог, админка.
- Кликабельная карта, бронь с сайта.
- Отдельный mobile-only layout (достаточно масштабируемого SVG).
- Редактирование PNG в рантайме.

## Принятые решения

| Тема | Решение |
|------|---------|
| Визуал зала | Растр `app/static/images/floor_plan.png` (1645×956 px) |
| Обёртка | Inline SVG, `viewBox="0 0 1645 956"` |
| Столы 1–8 | `circle` + `text` поверх номеров макета; кружок белый / `#d946ef`; цифра `#1a1a1a` / `#ffffff`; обводка кружка `rgba(0,0,0,0.25)` в free |
| Переговорка | Заливка **стола** (`rect` или `path`), белый / `#d946ef` |
| Текст на плане | Только цифры 1–8 в hotspots; **нет** статусных слов |
| Карточки | Без изменений (вариант A v2) |
| Легенда цветов | Не добавлять |

## Поведение UI

### Структура

```text
<div class="floor-plan-wrap">
  {% include "public/floor_plan.svg" %}
</div>
```

Корневой SVG:

- `class="floor-plan-svg"`, `xmlns`, `viewBox="0 0 1645 956"`, `width="100%"`, `preserveAspectRatio="xMidYMid meet"`.
- `role="img"`, `<title>`: «Схема коворкинга, занятость на ДД.ММ.ГГГГ».

Слои (снизу вверх):

1. **`<image>`** — `xlink:href` / `href` на `url_for('static', filename='images/floor_plan.png')`, размеры `1645`×`956`, без crop.
2. **Hotspots** — 9 групп `floor-unit` с `data-unit-id`, классы `floor-unit--free` / `floor-unit--busy` из `status_by_id`.

### Подсветка столов

Группа `<g id="desk-N" data-unit-id="desk-N" class="floor-unit …" aria-label="…">`:

- `<circle class="floor-unit__badge" cx cy r>` — радиус **~22–28** в координатах viewBox (подгонка перекрывает белый круг PNG).
- `<text class="floor-unit__label">N</text>` — по центру круга.

CSS остаётся в `availability-v2.css` (как в реализации 2026-11-20): селекторы `.floor-unit--free/busy` для `.floor-unit__badge`, `.floor-unit__label`, `.floor-unit__table`.

### Переговорка

Группа `<g id="meeting-room" …>`:

- Один `<rect class="floor-unit__table">` (или `path`) поверх белого стола на макете.
- Стартовый ориентир bbox (до подгонки): `x="95" y="268" width="420" height="115" rx="14"` — **уточнить по PNG** при реализации.

### Удаляемое / не возвращать

- Векторный декор (стены, подписи комнат, L-столы), нарисованный вместо PNG.
- CSS/text overlays `floor-overlay-marker`.
- Зависимость схемы от несуществующего `floor-plan.png` (имя с дефисом).

## Архитектура

### `app/catalog/floor_plan_hotspots.py`

Единственный источник координат в **пикселях viewBox**:

```python
@dataclass(frozen=True)
class DeskHotspot:
    unit_id: str
    cx: float
    cy: float
    radius: float


@dataclass(frozen=True)
class MeetingTableHotspot:
    unit_id: str
    x: float
    y: float
    width: float
    height: float
    rx: float
```

Начальные координаты центров столов (пересчёт из бывших `%` оверлея × 1645 / 956):

| unit_id | cx | cy |
|---------|-----|-----|
| desk-1 | 690.9 | 392.2 |
| desk-2 | 690.9 | 573.6 |
| desk-3 | 954.1 | 573.6 |
| desk-4 | 954.1 | 392.2 |
| desk-5 | 1184.4 | 392.2 |
| desk-6 | 1184.4 | 573.6 |
| desk-7 | 1414.7 | 573.6 |
| desk-8 | 1414.7 | 392.2 |

`radius` по умолчанию `26.0`. Значения **калибруются** визуально против PNG.

Blueprint **не обязан** передавать hotspots в шаблон, если partial импортирует константы через Jinja-макрос/Python — предпочтение: передать `desk_hotspots` и `meeting_hotspot` из `public.availability` для тестируемости и явного контракта.

### Шаблон `floor_plan.svg`

- Подключение `<image>` через `{{ url_for('static', filename='images/floor_plan.png') }}`.
- Цикл по `desk_hotspots` + блок meeting room из `meeting_hotspot`.
- Jinja выставляет `floor-unit--free|busy` и `aria-label` как в spec 2026-11-20.

### Откат failed vector

Удалить из partial все `floor-decor` paths, макросы `desk_shape`, белые рамки комнат. Оставить только image + hotspots.

## Доступность

- `aria-label` на каждой `floor-unit`: `display_name` + короткий статус (как в карточках).
- Текстовый статус для SR дублируют **карточки**.

## Тестирование

| Проверка | Ожидание |
|----------|----------|
| `GET /availability` | 200, `floor-plan-svg`, `floor_plan.png` в `href` изображения |
| Нет legacy | Нет `floor-overlay-marker`, нет `floor-plan-img` как отдельного `<img>` вне SVG |
| Нет vector mock | В SVG нет текста «ПЕРЕГОВОРКА» / «ОСНОВНОЙ ЗАЛ» как вектор (они только на PNG) |
| Занятость | `data-unit-id="desk-2"` + `floor-unit--busy` при confirmed |
| Карточки | `unit-card` на месте |

Файл `tests/test_floor_plan_svg.py` переименовать в `tests/test_floor_plan_overlay.py` или обновить ассерты под `<image>`.

## Риски

| Риск | Смягчение |
|------|-----------|
| Hotspots не попадают в цифры | Калибровка в браузере на 360px и desktop |
| Двойная цифра (PNG + SVG text) | Круг достаточного `r` + непрозрачная заливка перекрывает PNG |
| Кэш static | При смене PNG — смена query/hash (при необходимости) |

## Связь с документами

- v2 UI: карточки, шапка — без изменений.
- [2026-11-20-availability-floor-svg-design.md](./2026-11-20-availability-floor-svg-design.md) — **устарела**, не реализовывать.