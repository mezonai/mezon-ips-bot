from asyncio import current_task
from datetime import datetime, timezone
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_scoped_session,
    create_async_engine,
)
from sqlalchemy.orm import sessionmaker

from app.core.settings.app import app_settings


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


db_url = str(app_settings.db_uri)
engine_kwargs = {
    "future": True,
}

if db_url.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"timeout": 30}
else:
    engine_kwargs.update(
        {
            "pool_size": 30,
            "max_overflow": 5,
            "pool_pre_ping": True,
        }
    )

engine = create_async_engine(
    url=db_url,
    **engine_kwargs,
)

async_session_factory = async_scoped_session(
    sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    ),
    scopefunc=current_task,
)
