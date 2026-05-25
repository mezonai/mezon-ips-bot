# AGENTS.md

## Read Order
- Start here for fast repo context.
- Read `docs/architecture.md` for code map.
- Read one focused doc only if task needs it:
  - `docs/commands.md`
  - `docs/setup.md`
  - `docs/development.md`
  - `docs/operations.md`
  - `docs/forking-guide.md`

## Runbook
- Python version: `3.13`
- Setup: `uv sync`
- Run app: `python run.py --reload`
- Lint: `ruff check .`
- Format: `ruff format .`
- Tests: `pytest`
- DB only: `docker compose -f docker-compose.db.yml up -d db`
- Full stack: `docker compose up`
- Migrations: `alembic revision --autogenerate -m "message"` then `alembic upgrade head`

## High-Signal Repo Facts
- Entry point: `run.py`
- App factory/lifespan: `app/main.py`
- DI container is registration boundary: `app/dependencies/container.py`
- Message routing: `app/services/bot/handler_manager.py`
- Current registered handlers: `ExpertHandler`, `ProgramHandler`
- Top-level bot commands: `*expert`, `*program`, `*contract`
- Subcommands parsed inside handler methods, not separate decorated commands
- Mention aliases only work for mention-triggered messages
- `MEZON_BOT_REQUIRE_MENTION=true` makes bot ignore unmentioned messages
- FastAPI docs/OpenAPI enabled only when `APP_ENV=dev`

## Command Workflow Rules
- Empty invocation path must return help for each top-level command.
- If command surface changes, update handler help text, `docs/commands.md`, and tests.
- For command changes, cover help path and main success path.

## Data And Runtime Notes
- `.env` loaded with override behavior
- Required env keys: `APP_ENV`, `DB_URI`, `MEZON_CLIENT_ID`, `MEZON_API_KEY`
- Local repo defaults use database `ips-bot`
- SQLAlchemy is async; session factory scoped to `asyncio.current_task`
- Alembic scripts live in `app/database/migrations`
- Alembic URL comes from `app_settings.db_uri`, not placeholder in `alembic.ini`

## Files Requiring Care
- Word templates: `template/Template_HDCG.docx`, `template/Template_BBNT.docx`
- Generated exports write under `exports/`; do not commit unless asked
- `Dockerfile` includes `template/`; keep that true for export-related changes
- Ignore `mezon_ips_bot.egg-info/`; may be stale

## When Adding New Handler
1. Add provider in `app/dependencies/container.py`.
2. Add provider to `handler_manager` list.
3. Add help-path test.
4. Add main success-path test.

## Doc Discipline
- Keep root `README.md` short.
- Put durable operational or contributor detail under `docs/`.
- Prefer updating focused page over dumping more context into `AGENTS.md`.
