# Дизайн: полоса 7 дней + кнопка «Календарь» (unified)

**Дата:** 2026-11-21  
**Статус:** утверждён пользователем (вариант A — без десктоп-сетки)  
**Родительский scope:** горизонт +30 из [2026-11-21-public-availability-31-day-window-design.md](./2026-11-21-public-availability-31-day-window-design.md)

## Цель

На `/availability` одна строка: слева **7 чипов** (сегодня…+6), справа **кнопка «Календарь»** на всех брейкпоинтах. Выбор до **+30** — нативный `input type="date"` (`min`/`max`). **Без** HTML-сетки месяца на десктопе.

## Поведение

- `build_seven_day_strip(today)`; горизонт `clamp` +30 без изменений.
- Flex: `.availability-date-toolbar` — `day-strip` (`flex: 1`, overflow-x) + `.availability-calendar-trigger`.
- Кнопка вызывает `showPicker()` / `click()` на скрытом `input type="date"`; `change` → redirect `?date=`.
- Активный чип только если выбранный день в ближайших 7.

## Удалить

- Шаблон `aside.availability-month-calendar`, query `calendar_month`, `month_calendar` в view.
- Модуль `app/services/month_calendar.py`, тесты `test_month_calendar.py`.
- CSS `.availability-month-calendar*`, мобильный-only wrapper `d-md-none` у кнопки.

## Тесты

- HTML: `availability-date-toolbar`, `availability-calendar-open`, нет `availability-month-calendar`.
- Горизонт и полоса — без изменений.