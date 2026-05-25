# Architecture

## Runtime Shape

Flow:

1. `run.py` starts `uvicorn` for `app.main:app`
2. `app/main.py` builds `FastAPI` app and lifespan
3. Lifespan creates `Container`, logs Mezon client in, registers callbacks
4. `HandlerManager` routes channel messages and button-click events
5. Handlers call services, services call repositories, repositories use async SQLAlchemy session factory

## Main Boundaries

- App entry: `run.py`
- App factory and lifespan: `app/main.py`
- DI container: `app/dependencies/container.py`
- Message routing: `app/services/bot/handler_manager.py`
- Handlers: `app/services/bot/handlers/`
- Services: `app/services/{expert,program,contract,word_export}/`
- Repositories: `app/database/repositories/`
- Models and migrations: `app/database/models/`, `app/database/migrations/`

## Dependency Injection

`app/dependencies/container.py` is registration boundary.

Current wired singletons/factories include:

- `MezonClient`
- repositories for expert, contract, program
- services for expert, contract, program, Word export, S3 upload
- handlers: `ExpertHandler`, `ProgramHandler`
- `HandlerManager`

If adding handler:

1. create provider in container
2. add provider to `providers.List(...)` for `handler_manager`
3. add or update help path tests

## Command Routing

`HandlerManager`:

- ignores self-messages
- optionally requires mention
- strips leading mention tokens
- maps top-level command to decorated handler method
- supports alias lookup only for mention-triggered messages
- replies with available commands when bot is mentioned without content

Top-level command map today:

- `*expert`
- `*program`
- `*contract`

## HTTP API

Routers mounted under `app_settings.api_v1_prefix`, currently `/api/v1`.

Endpoints:

- `GET /api/v1/health` returns `{"status": "ok", "version": ...}`
- `GET /api/v1/bot/status` returns Mezon client initialization state

OpenAPI/docs are enabled only in `dev` mode.

## Files With Special Handling

- Word templates: `template/Template_HDCG.docx`, `template/Template_BBNT.docx`
- Generated exports: runtime output under `exports/`
- Container image must include `template/` when export behavior matters
