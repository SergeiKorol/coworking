# coworking

Сайт-визитка коворкинга: публичная занятость и админка ручных броней (Flask + SQLite).

## Документация

- [Дизайн](docs/superpowers/specs/2026-11-10-coworking-flask-design.md)
- [План реализации](docs/superpowers/plans/2026-11-10-coworking-flask.md)

## Локальный запуск

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
# отредактируйте .env
set FLASK_APP=wsgi.py
flask db init
flask db migrate -m "create booking table"
flask db upgrade
flask --app wsgi run
```

Откройте http://127.0.0.1:5000/ и `/availability`. Админка: `/admin/login`.

## Тесты

```bash
pytest -v
```

## PythonAnywhere

1. Загрузите репозиторий, создайте virtualenv, `pip install -r requirements.txt`.
2. В Web → WSGI укажите `wsgi.py` (объект `app`).
3. Задайте переменные окружения в разделе env / в файле (см. `.env.example`).
4. Выполните `flask db upgrade` в консоли PA.
5. Статика: `app/static` через PA static mapping при необходимости.

## HelioHost

Аналогично: WSGI на `wsgi.py`, SQLite в `instance/` с правами записи на каталог `instance/`.

## Перенос на платный хостинг

Замените `DATABASE_URL` (например PostgreSQL), выполните миграции, обновите WSGI и секреты.
