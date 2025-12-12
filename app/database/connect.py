from asyncio import current_task
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_scoped_session,
    create_async_engine,
)
from sqlalchemy.orm import sessionmaker

from app.core.settings.app import app_settings

engine = create_async_engine(
    url=str(app_settings.db_uri),
    pool_size=30,
    max_overflow=5,
    future=True,
    pool_pre_ping=True,
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
