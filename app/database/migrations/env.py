import asyncio
import pathlib
import sys
from datetime import datetime, timezone
from logging.config import fileConfig

from alembic import context
from dotenv import load_dotenv
from sqlalchemy import engine_from_config, pool, event
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.ext.asyncio import AsyncEngine

from app.core.settings.app import app_settings
from app.database.models.rwmodel import RWModel


# Register global listener to define "now" function for SQLite during migrations
@event.listens_for(Engine, "connect")
def register_sqlite_functions(dbapi_connection, connection_record):
    if hasattr(dbapi_connection, "create_function"):
        dbapi_connection.create_function(
            "now", 0, lambda: datetime.now(timezone.utc).isoformat()
        )
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.close()


load_dotenv(override=True)
sys.path.append(str(pathlib.Path(__file__).resolve().parents[3]))

DATABASE_URI = str(app_settings.db_uri).replace("%", "%%")

print(DATABASE_URI, "============")

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = RWModel.metadata

config.set_main_option("sqlalchemy.url", DATABASE_URI)


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        render_as_batch=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    connectable = AsyncEngine(
        engine_from_config(
            config.get_section(config.config_ini_section),
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
            future=True,
        )
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
