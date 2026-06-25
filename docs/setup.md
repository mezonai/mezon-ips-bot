# Setup

## Prerequisites

- Python `3.13`
- `uv` (fast Python toolchain manager)
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
- `DB_URI` (defaults to `sqlite+aiosqlite:///ips-bot.db`)
- `MEZON_CLIENT_ID`
- `MEZON_API_KEY`

Optional values:

- `MEZON_BOT_REQUIRE_MENTION`
- SMB local file storage configurations (`SMB_SHARE_PATH`, `SMB_PUBLIC_URL_BASE`)

## Database

Tables are created in the local SQLite database file by running migrations:

```bash
uv run alembic upgrade head
```

## Run Application

```bash
uv run python run.py --reload
```

Default local endpoints:

- Health: `GET /api/v1/health`
- Bot status: `GET /api/v1/bot/status`
- Swagger UI (dev only): `GET /docs` and `GET /redoc`
