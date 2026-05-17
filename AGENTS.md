# AGENTS.md

## Commands
- Python version is 3.13 (`.python-version`, `pyproject.toml`). Prefer `uv sync` for setup; lockfile is `uv.lock`.
- Run app: `python run.py --reload` (starts `uvicorn` on `app.main:app`, default `0.0.0.0:8000`).
- Lint/format: `ruff check .` and `ruff format .`.
- Tests: `pytest`; focused tests: `pytest tests/test_word_export.py` or `pytest tests/test_expert_handler_acceptance.py::TestHandleAcceptanceReport::test_handles_contract_not_found`.
- DB only: `docker compose -f docker-compose.db.yml up -d db`; full local stack: `docker compose up`.
- Migrations: `alembic revision --autogenerate -m "message"` then `alembic upgrade head`.

## Runtime/config gotchas
- `.env` is loaded with override in settings; required keys: `APP_ENV`, `DB_URI`, `MEZON_CLIENT_ID`, `MEZON_API_KEY`. Optional S3 keys are in `app/core/settings/app.py`.
- README `.env.example` uses database `mezon_bot`, but docker compose uses `ips-bot`; align `DB_URI` with how Postgres was started.
- FastAPI docs/OpenAPI are enabled only when `APP_ENV=dev`.
- App startup logs in to Mezon and registers message/button callbacks in lifespan; tests usually mock Mezon rather than starting the app.

## Architecture notes
- Entrypoints: `run.py` -> `app.main:app`; app factory/lifespan in `app/main.py`.
- DI container is the real registration boundary (`app/dependencies/container.py`): repositories, services, `MezonClient`, and bot handlers are wired there.
- Current registered message handlers are `ExpertHandler` and `ProgramHandler`; adding a new handler requires a provider plus adding it to `handler_manager`'s `providers.List(...)`.
- Commands are decorator-driven with `@command(...)` in `app/services/bot/handlers/base.py`; the handler manager parses the first token and supports aliases only for mention-triggered messages.
- Current top-level bot commands are `*expert`, `*program`, and `*contract`; subcommands are parsed inside those handler methods, not as separate decorated commands.
- `MEZON_BOT_REQUIRE_MENTION=true` makes the bot ignore unmentioned messages; mentioned aliases strip command prefixes (`expert` can map to `*expert`).
- Workflow rule for bot commands: when adding a new top-level command or new subcommand flow, always provide a help response for the empty invocation path (for example `*expert`, `*program`, `*contract`) instead of returning a generic syntax error or silently ignoring the message.
- Help coverage is part of the acceptance criteria for command changes: update the handler help text, update docs if command surface changes, and add or update tests for the empty-invocation/help path plus the main success path.

## Database/migrations
- SQLAlchemy is async; `async_session_factory` is an `async_scoped_session` scoped to `asyncio.current_task`.
- Alembic scripts live in `app/database/migrations` (non-default path from `alembic.ini`).
- Alembic URL comes from `.env`/`app_settings.db_uri`, not the placeholder in `alembic.ini`.
- Migration metadata target is `RWModel.metadata`; ensure new model modules are imported/exported so autogenerate sees them.

## Templates and generated files
- Word export depends on checked-in templates `template/Template_HDCG.docx` and `template/Template_BBNT.docx`.
- Export flows write generated `.docx` files under `exports/`; avoid committing generated outputs unless explicitly requested.
- Current `Dockerfile` copies only `app/`, `run.py`, and `alembic.ini`; if changing Word export in containers, account for missing `template/` in the image.

## Repo hygiene
- Do not rely on `mezon_ips_bot.egg-info/`; it is ignored packaging output and may list stale files.
- `scripts/`, `mezon-cache/`, `.env`, `.venv`, and `*.egg-info/` are ignored; do not place durable source changes there.
