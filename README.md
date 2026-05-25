# Mezon IPS Bot

FastAPI-based Mezon bot for expert, program, and contract workflows.

## What It Does

- Handles Mezon channel commands through registered bot handlers
- Manages experts, programs, and expert contracts
- Exposes small health/status HTTP API
- Generates Word documents from checked-in templates
- Supports optional S3-compatible upload flow for generated files

## Documentation

- Docs hub: [`docs/README.md`](docs/README.md)
- Local setup: [`docs/setup.md`](docs/setup.md)
- Bot commands: [`docs/commands.md`](docs/commands.md)
- Architecture: [`docs/architecture.md`](docs/architecture.md)
- Development workflow: [`docs/development.md`](docs/development.md)
- Runtime and deployment notes: [`docs/operations.md`](docs/operations.md)
- Forking guide: [`docs/forking-guide.md`](docs/forking-guide.md)

## Quick Start

```bash
uv sync
cp .env.example .env
docker compose -f docker-compose.db.yml up -d db
alembic upgrade head
python run.py --reload
```

Default local API:

- Health: `http://localhost:8000/api/v1/health`
- Bot status: `http://localhost:8000/api/v1/bot/status`
- Swagger UI in dev only: `http://localhost:8000/docs`

## Core Commands

- `*expert`
- `*program`
- `*contract`

Each top-level command returns help when invoked without subcommand. Full command reference lives in [`docs/commands.md`](docs/commands.md).

## Tech Stack

- Python 3.13
- FastAPI
- SQLAlchemy async + asyncpg
- Alembic
- dependency-injector
- `mezon-sdk`

## Repo Notes

- Entry point: `run.py`
- App factory: `app/main.py`
- DI container: `app/dependencies/container.py`
- Checked-in Word templates: `template/`
- Generated exports: `exports/` at runtime
