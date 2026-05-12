from typing import Optional, List

from sqlalchemy import func, select

from app.database.repositories.base import BaseRepository
from app.database.models.program import Program


class ProgramRepository(BaseRepository):
    """Repository for program data access."""

    async def create_program(self, program: Program) -> Program:
        """Create a new program."""
        async with self._get_session() as session:
            session.add(program)
            await session.commit()
            await session.refresh(program)
            return program

    async def get_program_by_id(self, program_id: int) -> Optional[Program]:
        """Get a program by ID."""
        async with self._get_session() as session:
            result = await session.execute(
                select(Program).where(Program.id == program_id)
            )
            return result.scalars().first()

    async def get_program_by_code(self, program_code: str) -> Optional[Program]:
        """Get a program by its code."""
        async with self._get_session() as session:
            result = await session.execute(
                select(Program).where(
                    func.upper(Program.program_code) == program_code,
                    Program.deleted_at.is_(None),
                )
            )
            return result.scalars().first()

    async def list_programs(self) -> List[Program]:
        """List all non-deleted programs."""
        async with self._get_session() as session:
            result = await session.execute(
                select(Program)
                .where(Program.deleted_at.is_(None))
                .order_by(Program.created_at.desc())
            )
            return result.scalars().all()

    async def update_program(self, program: Program) -> Program:
        """Update an existing program."""
        async with self._get_session() as session:
            session.add(program)
            await session.commit()
            await session.refresh(program)
            return program

    async def delete_program(self, program_id: int) -> bool:
        """Soft-delete a program."""
        from datetime import datetime, timezone

        async with self._get_session() as session:
            result = await session.execute(
                select(Program).where(Program.id == program_id)
            )
            program = result.scalars().first()
            if program:
                program.deleted_at = datetime.now(timezone.utc)
                await session.commit()
                return True
            return False
