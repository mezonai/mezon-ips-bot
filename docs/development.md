# Development

## Core Commands

```bash
uv sync
ruff check .
ruff format .
pytest
```

Focused test examples:

```bash
pytest tests/test_word_export.py
pytest tests/test_expert_handler_acceptance.py::TestHandleAcceptanceReport::test_handles_contract_not_found
```

## Coding Rules For This Repo

- Keep changes small and local when possible
- Update docs when command surface or workflow changes
- Do not commit generated files under `exports/` unless explicitly needed
- Do not rely on `mezon_ips_bot.egg-info/`; packaging output may be stale

## Command Change Acceptance

When adding or changing bot command flow:

1. provide help response for empty invocation path
2. update handler help text
3. update `docs/commands.md` if command surface changed
4. add or update tests for help path and main success path

## Migrations

```bash
alembic revision --autogenerate -m "message"
alembic upgrade head
```

Notes:

- Alembic scripts live in `app/database/migrations`
- Alembic URL comes from `.env` via `app_settings.db_uri`
- Migration metadata target is `RWModel.metadata`
- Import/export new model modules so autogenerate sees them

## Testing Strategy

- Prefer focused tests around touched handler or service
- App startup logs in to Mezon during lifespan, so tests usually mock Mezon instead of starting full app
- If command help behavior changes, cover empty invocation path explicitly

## Adding New Handler

1. add handler in `app/services/bot/handlers/`
2. decorate top-level command method with `@command(...)`
3. register provider in `app/dependencies/container.py`
4. add provider into `handler_manager` list
5. add help-path and success-path tests

## Useful File Map

- settings: `app/core/settings/app.py`
- bot handlers: `app/services/bot/handlers/`
- bot service: `app/services/bot/service.py`
- repositories: `app/database/repositories/`
- tests: `tests/`
