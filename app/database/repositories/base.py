from typing import Callable
from sqlalchemy.ext.asyncio import AsyncSession


class BaseRepository:
    """Base Repository for all repositories."""

    def __init__(self, session_factory: Callable[[], AsyncSession]) -> None:
        self._session_factory = session_factory

    def _get_session(self) -> AsyncSession:
        return self._session_factory()
