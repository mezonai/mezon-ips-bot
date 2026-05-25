# Forking Guide

Use this guide when reusing this repo as base for another Mezon Python bot.

Goal: keep stable infrastructure, replace business domain.

Stable infrastructure:

- FastAPI lifespan
- Mezon SDK login/callback flow
- dependency-injector container
- async SQLAlchemy repositories
- command handler routing
- interactive forms/buttons
- Alembic migrations
- focused handler/service tests

## Core Rules

- Keep Python `3.13` and install with `uv sync`.
- Keep entrypoint `run.py -> app.main:app`.
- Keep FastAPI as host/lifecycle only; do not put bot business logic in HTTP routes.
- Keep `app/dependencies/container.py` as registration boundary.
- Keep async end-to-end for callbacks, services, repositories, and SQLAlchemy.
- Replace domain through model, repository, service, handler, docs, and tests.
- Write generated files under `exports/` and do not commit them unless asked.

## Runtime And Settings

Settings live in `app/core/settings/app.py` and `.env` is loaded with override behavior.

Required env keys:

- `APP_ENV`
- `DB_URI`
- `MEZON_CLIENT_ID`
- `MEZON_API_KEY`

Common optional keys:

- `MEZON_BOT_REQUIRE_MENTION`
- `S3_ENDPOINT_URL`
- `S3_ACCESS_KEY`
- `S3_SECRET_KEY`
- `S3_BUCKET_NAME`
- `S3_REGION`
- `S3_PUBLIC_URL_BASE`

Docker notes:

- local compose files use database `ips-bot`
- `Dockerfile` copies `app/`, `run.py`, `alembic.ini`, and `template/`
- copy extra templates/static assets into image if new bot needs them

## Startup Flow

Keep `app/main.py` flow:

1. create `Container()`
2. wire container for API modules
3. get `mezon_client` from container
4. call `await mezon_client.login()`
5. get `handler_manager` from container
6. register `on_channel_message` and `on_message_button_clicked` callbacks
7. save container/client/handler manager in `app.state`
8. disconnect Mezon client during shutdown

Do not manually construct handlers or services in `main.py`.

## Add Domain

When adding domain `<domain>`:

1. create SQLAlchemy model in `app/database/models/<domain>.py`
2. export model in `app/database/models/__init__.py`
3. create repository in `app/database/repositories/<domain>.py`
4. create service in `app/services/<domain>/service.py`
5. create handler in `app/services/bot/handlers/<domain>.py`
6. register repository/service/handler in `Container`
7. add handler provider to `handler_manager` providers list
8. add tests for help path and main success path

Container pattern:

```python
domain_repository = providers.Singleton(
    DomainRepository,
    session_factory=db_session_factory,
)

domain_service = providers.Singleton(
    DomainService,
    domain_repository=domain_repository,
)

domain_handler = providers.Singleton(
    DomainHandler,
    client=mezon_client,
    domain_service=domain_service,
)

handler_manager = providers.Singleton(
    HandlerManager,
    handlers=providers.List(
        expert_handler,
        program_handler,
        domain_handler,
    ),
    client_id=app_settings.mezon_client_id,
    require_mention=app_settings.mezon_bot_require_mention,
)
```

## Command Handler Pattern

Commands use `@command(...)` from `app/services/bot/handlers/base.py`.

Minimal handler:

```python
from typing import Any

from app.services.bot.handlers.base import BaseMessageHandler, command


class TaskHandler(BaseMessageHandler):
    def __init__(self, client, task_service):
        super().__init__(client)
        self.task_service = task_service

    @command("*task")
    async def handle_task(
        self,
        message: Any,
        subcmd: str = None,
        rest: str = None,
    ) -> None:
        if not subcmd:
            await self.reply_message(
                message,
                "📋 **Quản lý task**\n\n"
                "• `*task list` - Danh sách\n"
                "• `*task add` - Thêm mới",
            )
            return

        if subcmd == "list":
            await self._handle_list(message)
        elif subcmd == "add":
            await self._handle_add(message)
        else:
            await self.reply_message(
                message,
                f"❌ Lệnh con không hợp lệ: `{subcmd}`.\n"
                "Dùng `*task` để xem danh sách lệnh.",
            )
```

Command UX rules:

- every top-level command must return help when invoked without subcommand
- subcommands stay inside handler method, not separate decorated commands, unless command truly belongs to another top-level domain
- invalid subcommand should point user back to top-level help
- command surface changes require handler help, `docs/commands.md`, and tests

Argument parsing notes:

- first token is top-level command
- parameters after `self, message` are parsed from message body
- final `str` parameter receives remaining text
- `int` and `float` consume one token
- parameter with default is optional; without default is required

Mention mode:

- `MEZON_BOT_REQUIRE_MENTION=true` ignores unmentioned messages
- mention-triggered messages can use alias without prefix, for example `@Bot expert list`
- prefix stripping uses character set `*!/@`

## Buttons And Forms

Current handlers use Mezon interactive builders:

- `InteractiveBuilder`
- `ButtonBuilder`
- `InteractiveMessageProps`
- `MessageActionRow`
- `MessageComponent`
- `ButtonMessageStyle`

Form pattern:

```python
form = InteractiveBuilder("Tạo item")
form.set_description("Điền thông tin bên dưới")
form.set_color("#5865F2")
form.add_input_field("name", "Tên", placeholder="Tên item")

await self.reply_message(
    message,
    "Vui lòng điền form:",
    embeds=[InteractiveMessageProps(**form.build())],
    components=self._build_buttons([
        ("save_item", "Lưu", ButtonMessageStyle.SUCCESS),
        ("cancel", "Hủy", ButtonMessageStyle.DANGER),
    ]),
)
```

Button pattern:

```python
async def handle_button_click(self, event) -> None:
    extra_data = form_tracker.parse_extra_data(event.extra_data)

    if event.button_id == "cancel":
        await self.edit_message(event.channel_id, event.message_id, "Đã hủy.", components=[])
        return

    if event.button_id == "save_item":
        await self._handle_save_item(event, extra_data)
        return

    if event.button_id.startswith("edit_item:"):
        item_id = int(event.button_id.split(":")[1])
        await self._handle_edit_item(event, item_id, extra_data)
        return
```

Current gotcha:

- `HandlerManager.handle_button_click()` routes only `ExpertHandler` and `ProgramHandler`
- if adding new button-capable handler, refactor to capability-based routing or update current tuple

Preferred routing shape:

```python
for handler, _info in self._command_map.values():
    if hasattr(handler, "handle_button_click"):
        await handler.handle_button_click(event)
```

## Service Layer

Service should hold business rules, validation, and ORM-to-DTO mapping. Handler should coordinate input/output only.

DTO pattern:

```python
from dataclasses import dataclass


@dataclass
class TaskData:
    id: int
    title: str
    description: str | None = None
```

Service pattern:

```python
class TaskService:
    def __init__(self, task_repository):
        self._repository = task_repository

    async def create_task(self, data: TaskData) -> TaskData:
        task = Task(title=data.title, description=data.description)
        created = await self._repository.create(task)
        return self._to_data(created)

    def _to_data(self, task: Task) -> TaskData:
        return TaskData(
            id=task.id,
            title=task.title,
            description=task.description,
        )
```

Keep these in service layer:

- normalize codes before save/lookup
- duplicate checks
- domain calculations
- DTO conversion

Do not let handlers mutate ORM objects directly.

## Repository And Database

DB stack:

- async SQLAlchemy engine in `app/database/connect.py`
- `async_session_factory` scoped by `asyncio.current_task`
- repositories receive `session_factory`
- each repository method opens session via `async with self._get_session() as session`
- create/update/delete methods commit in repository
- soft-delete uses `deleted_at`

Repository pattern:

```python
from sqlalchemy import select

from app.database.models.task import Task
from app.database.repositories.base import BaseRepository


class TaskRepository(BaseRepository):
    async def create(self, task: Task) -> Task:
        async with self._get_session() as session:
            session.add(task)
            await session.commit()
            await session.refresh(task)
            return task

    async def get_by_id(self, task_id: int) -> Task | None:
        async with self._get_session() as session:
            result = await session.execute(
                select(Task).where(Task.id == task_id, Task.deleted_at.is_(None))
            )
            return result.scalars().first()
```

Model pattern:

```python
from sqlalchemy import Column, Index, Integer, String

from app.database.models.common import DateTimeModelMixin
from app.database.models.rwmodel import RWModel


class Task(RWModel, DateTimeModelMixin):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False)
    description = Column(String(1000), nullable=True)

    __table_args__ = (Index("ix_tasks_title", "title"),)
```

Migration commands:

```bash
alembic revision --autogenerate -m "add tasks table"
alembic upgrade head
```

Migration notes:

- migration scripts live in `app/database/migrations`
- Alembic URL comes from `app_settings.db_uri`
- metadata target is `RWModel.metadata`
- import/export new models so autogenerate sees them

## HTTP API

HTTP API should stay thin for health/status/admin endpoints.

Current endpoints:

- `GET /api/v1/health`
- `GET /api/v1/bot/status`

When adding route:

1. create file in `app/api/v1/`
2. register router in `app/api/v1/__init__.py`
3. add module to `Container.wiring_config.modules` if dependency injection needed

Do not process bot commands through HTTP if Mezon callback flow already covers them.

## File Export And Upload

Current export stack:

- `WordExportService` uses `docxtpl`
- contract template: `template/Template_HDCG.docx`
- acceptance template: `template/Template_BBNT.docx`
- output directory: `exports/`
- upload uses `S3UploadService` when configured, otherwise Mezon upload fallback

Export rules:

- keep rendering logic in service, not handler
- ensure templates are copied into Docker image
- sanitize output filename if using user input
- do not commit files under `exports/`

## Tests

Prefer mocked service/client tests instead of starting full app.

Useful commands:

```bash
pytest
pytest tests/test_word_export.py
pytest tests/test_expert_handler_acceptance.py::TestHandleAcceptanceReport::test_handles_contract_not_found
```

Recommended coverage:

- service rules: duplicate, normalize, date validation
- export context mapping
- handler flow via `MagicMock`/`AsyncMock`
- button routing and `button_id` dispatch
- repository integration only when SQL behavior matters

Minimal mock client:

```python
from unittest.mock import AsyncMock, MagicMock


client = MagicMock()
client.channels = MagicMock()
channel = AsyncMock()
channel.send = AsyncMock()
client.channels.fetch = AsyncMock(return_value=channel)
client.upload_file = AsyncMock()
```

## Fork Checklist

1. rename project in `pyproject.toml`, `README.md`, and deployment metadata if needed
2. update `app_settings.app_name`, `title`, and `version`
3. define main domain
4. create model and export it
5. create and review migration
6. create repository
7. create DTO and service
8. create handler with `BaseMessageHandler` and `@command`
9. implement `handle_button_click` if using buttons/forms
10. fix button routing for new handler if needed
11. register dependencies in `Container`
12. add tests for service and handler flows
13. run `ruff check .`, `ruff format .`, and `pytest`
14. run app with `python run.py --reload`
15. ensure Docker image copies required templates/static assets

## Gotchas

- command will not run if handler is not in `providers.List`
- Alembic may miss new tables if model is not imported/exported
- do not keep ORM objects across async sessions
- do not commit `.env`, `.venv`, `exports/`, or generated files
- test mention alias path when using `MEZON_BOT_REQUIRE_MENTION=true`
- button ids should have clear domain prefix like `save_task`, `edit_task:<id>`, `confirm_delete_task:<id>`
- multiple handlers can receive same button event today; handlers should return early for foreign button ids
- if app uses multiple workers, verify Mezon callbacks are not registered more than once

## Agent Prompt Template

```text
Hãy thêm domain <DOMAIN> vào bot Mezon dựa trên kiến trúc hiện tại.

Yêu cầu:
- Giữ FastAPI lifespan và DI container hiện tại.
- Tạo SQLAlchemy model + Alembic migration nếu cần lưu DB.
- Tạo repository async, service dataclass DTO, handler command.
- Command top-level là *<command>.
- Handler dùng @command trong BaseMessageHandler.
- Nếu có form/button, implement handle_button_click và đăng ký handler trong Container.
- Không đặt nghiệp vụ trong app/main.py hoặc route HTTP.
- Viết test cho service rule và handler flow.
- Chạy ruff check, ruff format, pytest.

Luồng mong muốn:
1. *<command> hiển thị help.
2. *<command> list liệt kê dữ liệu.
3. *<command> add mở interactive form.
4. Button save validate input và gọi service create.
5. edit/delete dùng button id có dạng edit_<domain>:<id>, confirm_delete_<domain>:<id>.
```
