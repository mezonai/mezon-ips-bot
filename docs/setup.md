# Setup

## Prerequisites

- Python `3.13`
- `uv`
- PostgreSQL, local or Docker
- Mezon bot credentials: `MEZON_CLIENT_ID`, `MEZON_API_KEY`

## Install

```bash
uv sync
```

## Configure Environment

```bash
cp .env.example .env
```

Required values in `.env`:

- `APP_ENV`
- `DB_URI`
- `MEZON_CLIENT_ID`
- `MEZON_API_KEY`

Optional values:

- `MEZON_BOT_REQUIRE_MENTION`
- S3-compatible upload settings in `app/core/settings/app.py`

## Database

Fastest local path:

```bash
docker compose -f docker-compose.db.yml up -d db
alembic upgrade head
```

Important:

- `.env.example` uses database `ips-bot`
- `docker-compose.yml` also uses database `ips-bot`
- Keep `DB_URI` aligned with how PostgreSQL was started

## Run Application

```bash
python run.py --reload
```

Default local endpoints:

- `GET /api/v1/health`
- `GET /api/v1/bot/status`
- `GET /docs` and `GET /redoc` only when `APP_ENV=dev`

## Full Local Stack

```bash
docker compose up
```

Notes:

- App container overrides `DB_URI` to point at service `db`
- App healthcheck calls `http://localhost:8000/api/v1/health`
