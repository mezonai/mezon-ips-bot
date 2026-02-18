# Laptrinhai Mezon Bot

A FastAPI-based bot template that connects to [Mezon](https://mezon.vn) and handles channel messages via a pluggable handler system. Includes an example **gold price** handler that responds to `!gold` commands with Vietnamese gold prices (SJC, PNJ, etc.).

## Features

- **Mezon integration** — Connects via [mezon-sdk](https://pypi.org/project/mezon-sdk/), listens for channel messages and routes them to handlers
- **Handler-based architecture** — Add new commands by implementing `BaseMessageHandler` and registering in the container
- **FastAPI** — REST API with health check and bot status endpoints
- **PostgreSQL** — Async SQLAlchemy + Alembic for gold price (and other) data
- **Dependency injection** — `dependency-injector` for wiring services, repositories, and handlers

## Prerequisites

- Python 3.13+
- PostgreSQL
- Mezon client ID and API key

## Installation

### Using uv (recommended)

```bash
uv sync
```

### Using pip

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e .
```

## Configuration

Copy the example env file and set your values:

```bash
cp .env.example .env
```

| Variable | Description |
|----------|-------------|
| `APP_ENV` | `dev` or `prod` (dev enables OpenAPI docs) |
| `MEZON_CLIENT_ID` | Your Mezon bot client ID |
| `MEZON_API_KEY` | Your Mezon API key |
| `DB_URI` | PostgreSQL connection string, e.g. `postgresql+asyncpg://user:pass@localhost:5432/mezon_bot` |

## Database setup

Create the database, then run migrations:

```bash
alembic upgrade head
```

## Running the app

```bash
python run.py
```

Options:

- `--host 0.0.0.0` — Bind address (default: `0.0.0.0`)
- `--port 8000` — Port (default: `8000`)
- `--reload` — Auto-reload on code changes
- `--workers 1` — Number of workers (default: `1`)

With reload (development):

```bash
python run.py --reload
```

The app will:

1. Start the FastAPI server
2. Log in to Mezon and attach the handler manager to channel messages
3. Respond to commands (e.g. `!gold`) in connected channels

## API

- **Health:** `GET /api/v1/health` — Health check
- **Bot status:** `GET /api/v1/bot/status` — Bot connection status
- **OpenAPI (dev only):** `GET /api/v1/openapi.json` — OpenAPI schema

## Bot commands

| Command | Description |
|---------|-------------|
| `!gold` | Today’s gold prices (TPHCM) |
| `!gold SJC` | SJC gold price only |
| `!gold PNJ` | PNJ gold price only |

## Project structure

```
app/
├── api/v1/              # FastAPI routes (health, bot)
├── core/settings/       # App settings (pydantic-settings)
├── database/            # SQLAlchemy models, connect, migrations, repositories
├── dependencies/        # DI container (container.py)
├── schemas/             # Pydantic schemas
├── services/
│   ├── bot/             # Mezon bot: HandlerManager, handlers (gold_price), base handler
│   └── gold_price/      # Gold price business logic
├── main.py              # FastAPI app + lifespan (Mezon login, handler wiring)
run.py                   # CLI entry (uvicorn)
```

## Adding a new command handler

1. **Create a handler** in `app/services/bot/handlers/` that extends `BaseMessageHandler`:
   - Implement `get_command()` (e.g. `"!hello"`)
   - Implement `async handle(message, content)` and call `reply_message` or `send_message`

2. **Register in the container** in `app/dependencies/container.py`:
   - Add a `providers.Singleton` for your handler
   - Add it to `HandlerManager`’s `handlers` list in `providers.List(...)`

3. **Wire modules** (if you add new API routes that use the container): add the module to `wiring_config.modules` in `Container`.

## Development

- Lint/format: `ruff check .` / `ruff format .`
- Migrations: `alembic revision --autogenerate -m "description"` then `alembic upgrade head`

## License

This project is licensed under the [MIT License](LICENSE).
