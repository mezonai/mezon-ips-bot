from typing import Optional, List

from sqlalchemy import select

from app.database.repositories.base import BaseRepository
from app.database.models.expert import Expert


class ExpertRepository(BaseRepository):
    """Repository for expert data access."""

    async def create(self, expert: Expert) -> Expert:
        """Create a new expert record."""
        async with self._get_session() as session:
            session.add(expert)
            await session.commit()
            await session.refresh(expert)
            return expert

    async def get_by_id(self, expert_id: int) -> Optional[Expert]:
        """Get expert by ID."""
        async with self._get_session() as session:
            result = await session.execute(
                select(Expert).where(Expert.id == expert_id)
            )
            return result.scalars().first()

    async def find_by_name(self, name: str) -> List[Expert]:
        """Find experts by expert_name (case-insensitive partial match)."""
        async with self._get_session() as session:
            result = await session.execute(
                select(Expert).where(Expert.expert_name.ilike(f"%{name}%"))
            )
            return result.scalars().all()

    async def find_by_id_number(self, id_number: str) -> Optional[Expert]:
        """Find expert by CCCD/id_number."""
        async with self._get_session() as session:
            result = await session.execute(
                select(Expert).where(Expert.id_number == id_number)
            )
            return result.scalars().first()

    async def update(self, expert: Expert) -> Expert:
        """Update an existing expert record."""
        async with self._get_session() as session:
            session.add(expert)
            await session.commit()
            await session.refresh(expert)
            return expert

    async def delete(self, expert_id: int) -> bool:
        """Soft-delete an expert record (set deleted_at)."""
        from datetime import datetime, timezone

        async with self._get_session() as session:
            result = await session.execute(
                select(Expert).where(Expert.id == expert_id)
            )
            expert = result.scalars().first()
            if expert:
                expert.deleted_at = datetime.now(timezone.utc)
                await session.commit()
                return True
            return False

    async def list_all(self, limit: int = 50) -> List[Expert]:
        """List all non-deleted experts."""
        async with self._get_session() as session:
            result = await session.execute(
                select(Expert)
                .where(Expert.deleted_at.is_(None))
                .order_by(Expert.expert_name)
                .limit(limit)
            )
            return result.scalars().all()
