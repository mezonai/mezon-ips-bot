from typing import Optional, List

from sqlalchemy import select

from app.database.repositories.base import BaseRepository
from app.database.models.professional import Professional


class ProfessionalRepository(BaseRepository):
    """Repository for professional (expert) data access."""

    async def create(self, professional: Professional) -> Professional:
        """Create a new professional record."""
        async with self._get_session() as session:
            session.add(professional)
            await session.commit()
            await session.refresh(professional)
            return professional

    async def get_by_id(self, professional_id: int) -> Optional[Professional]:
        """Get professional by ID."""
        async with self._get_session() as session:
            result = await session.execute(
                select(Professional).where(Professional.id == professional_id)
            )
            return result.scalars().first()

    async def find_by_name(self, name: str) -> List[Professional]:
        """Find professionals by expert_name (case-insensitive partial match)."""
        async with self._get_session() as session:
            result = await session.execute(
                select(Professional).where(Professional.expert_name.ilike(f"%{name}%"))
            )
            return result.scalars().all()

    async def find_by_id_number(self, id_number: str) -> Optional[Professional]:
        """Find professional by CCCD/id_number."""
        async with self._get_session() as session:
            result = await session.execute(
                select(Professional).where(Professional.id_number == id_number)
            )
            return result.scalars().first()

    async def update(self, professional: Professional) -> Professional:
        """Update an existing professional record."""
        async with self._get_session() as session:
            session.add(professional)
            await session.commit()
            await session.refresh(professional)
            return professional

    async def delete(self, professional_id: int) -> bool:
        """Soft-delete a professional record (set deleted_at)."""
        from datetime import datetime, timezone

        async with self._get_session() as session:
            result = await session.execute(
                select(Professional).where(Professional.id == professional_id)
            )
            professional = result.scalars().first()
            if professional:
                professional.deleted_at = datetime.now(timezone.utc)
                await session.commit()
                return True
            return False

    async def list_all(self, limit: int = 50) -> List[Professional]:
        """List all non-deleted professionals."""
        async with self._get_session() as session:
            result = await session.execute(
                select(Professional)
                .where(Professional.deleted_at.is_(None))
                .order_by(Professional.expert_name)
                .limit(limit)
            )
            return result.scalars().all()
