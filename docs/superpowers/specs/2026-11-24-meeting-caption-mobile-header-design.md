# Дизайн: подпись переговорки на плане + мобильная шапка v2

**Дата:** 2026-11-24  
**Статус:** утверждён пользователем  
**Заменяет (частично):** [2026-11-21-public-header-mobile-compact-design.md](./2026-11-21-public-header-mobile-compact-design.md)

## 1. Подпись переговорки

- SVG `<text class="floor-unit__caption">` в группе `meeting-room`.
- Текст: `16кв.м 10 посадочных мест`.
- Координаты в `MeetingTableHotspot`: `caption_x`, `caption_y`, `caption_font_size`.
- Цвета: `.floor-unit--free .floor-unit__caption { fill: #1a1a1a; }`, busy — `fill: #ffffff` (стол фуксия).

## 2. Мобильная шапка (≤768px)

- Строка 1: «Коворкинг» по центру (вариант A).
- Строка 2: горизонтальный flex — **слева логотип**, **справа колонка контактов**:
  - `.site-header__contacts`: `flex-direction: column`, адрес сверху, телефон снизу;
  - адрес допускает перенос (до ~2 строк), без однострочного ellipsis;
  - телефон: `white-space: nowrap`.
- Логотип видим; `max-height` ~36px на mobile; `gap` строки ~0.75rem.
- Десктоп (>768px): `display: contents` у `.site-header__row-mobile`, сетка без изменений.

## 3. Тесты

- HTML contains `floor-unit__caption` and `16кв.м`.
- CSS mobile: логотип не скрыт; у `.site-header__contacts` — `flex-direction: column`.