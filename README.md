# coworking

Сайт-визитка коворкинга: публичная занятость и админка ручных броней (Flask + SQLite).

## Документация

- [Дизайн](docs/superpowers/specs/2026-11-10-coworking-flask-design.md)
- [План реализации](docs/superpowers/plans/2026-11-10-coworking-flask.md)

## Локальный запуск

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements-dev.txt
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

Только для локальной разработки (`requirements-dev.txt` не используется на Amvera):

```bash
pip install -r requirements-dev.txt
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

## Replit (SQLite)

Проект рассчитан на **SQLite** в `instance/coworking.db`. Встроенную **production PostgreSQL** Replit для этого репозитория не используйте.

1. **Secrets** (Development и **Production**): скопируйте поля из `.env.example`.
   - Обязательно задайте `DATABASE_URL=sqlite:///instance/coworking.db`.
   - Удалите из Secrets любой `DATABASE_URL` с `postgresql://`, иначе приложение упадёт без `psycopg`.
   - Нужны: `FLASK_SECRET_KEY`, `ADMIN_USERNAME`, `ADMIN_PASSWORD`.
2. В каталоге Repl: `pip install -r requirements.txt`.
3. Один раз создайте таблицы:

   ```bash
   mkdir -p instance
   python -c "from wsgi import app; from app.extensions import db; \
   with app.app_context(): db.create_all(); print('OK')"
   ```

4. Локальный Run / Deploy: `python wsgi.py` (слушает `0.0.0.0:5000`, снаружи порт **80** — см. `.replit`).
5. На экране Deploy **не** включайте «production database» с копированием из dev Postgres — для SQLite это не нужно.

В репозитории лежит `.replit` без лишнего проброса порта `8080`.

## Amvera Cloud

Документация: [Python + pip](https://docs.amvera.ru/applications/environments/python-pip.html), [пример Flask](https://docs.amvera.ru/general/examples/python-flask.html).

1. В [cloud.amvera.ru](https://cloud.amvera.ru/) создайте приложение и привяжите git-репозиторий (или `git push` на remote Amvera).
2. В репозитории есть **`amvera.yml`**: gunicorn → **`wsgi:app`**, порт **5000**, `persistenceMount: /data`.
3. В **переменных окружения** приложения (не `.env` в git) задайте поля из `.env.example`:
   - обязательно: `FLASK_SECRET_KEY`, `ADMIN_USERNAME`, `ADMIN_PASSWORD`;
   - **`DATABASE_URL=sqlite:////data/coworking.db`** — SQLite на постоянном диске Amvera.
4. Сборка ставит только **`requirements.txt`** (без pytest).
5. Перед gunicorn запускается **`python -m app.db_bootstrap`** (миграции + reconcile, если ранее вызывали `create_all` в консоли).
6. Проверьте публичную страницу `/availability` и вход `/admin/login`.

Если 502/503: убедитесь, что gunicorn слушает `0.0.0.0` и `containerPort` совпадает с портом в `--bind` (см. [FAQ Amvera](https://docs.amvera.ru/general/FAQ/502-503-error.html)).

## Перенос на платный хостинг

Замените `DATABASE_URL` (например PostgreSQL), выполните миграции, обновите WSGI и секреты.
