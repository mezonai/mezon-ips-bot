from typing import Optional, List
from dataclasses import dataclass
from datetime import date as date_type

from app.database.repositories.program import ProgramRepository
from app.database.models.program import Program


@dataclass
class ProgramData:
    """Data class for program information."""

    id: int
    program_code: str
    name: str
    summary_activities: Optional[str] = None
    activity_purpose: Optional[str] = None
    end_date: Optional[date_type] = None


class ProgramService:
    """Service for program operations."""

    def __init__(self, program_repository: ProgramRepository):
        self._repository = program_repository

    async def create_program(self, data: ProgramData) -> ProgramData:
        """Create a new program."""
        program = Program(
            program_code=data.program_code,
            name=data.name,
            summary_activities=data.summary_activities,
            activity_purpose=data.activity_purpose,
            end_date=data.end_date,
        )
        created = await self._repository.create_program(program)
        return self._to_data(created)

    async def get_program_by_id(self, program_id: int) -> Optional[ProgramData]:
        """Get a program by ID."""
        program = await self._repository.get_program_by_id(program_id)
        if program is None:
            return None
        return self._to_data(program)

    async def get_program_by_code(self, program_code: str) -> Optional[ProgramData]:
        """Get a program by its code."""
        program = await self._repository.get_program_by_code(program_code)
        if program is None:
            return None
        return self._to_data(program)

    async def list_programs(self) -> List[ProgramData]:
        """List all programs."""
        programs = await self._repository.list_programs()
        return [self._to_data(p) for p in programs]

    async def update_program(
        self, program_id: int, data: ProgramData
    ) -> Optional[ProgramData]:
        """Update a program's information."""
        program = await self._repository.get_program_by_id(program_id)
        if program is None:
            return None

        program.program_code = data.program_code
        program.name = data.name
        program.summary_activities = data.summary_activities
        program.activity_purpose = data.activity_purpose
        program.end_date = data.end_date

        updated = await self._repository.update_program(program)
        return self._to_data(updated)

    async def delete_program(self, program_id: int) -> bool:
        """Soft-delete a program."""
        return await self._repository.delete_program(program_id)

    def _to_data(self, program: Program) -> ProgramData:
        """Convert ORM model to data class."""
        return ProgramData(
            id=program.id,
            program_code=program.program_code,
            name=program.name,
            summary_activities=program.summary_activities,
            activity_purpose=program.activity_purpose,
            end_date=program.end_date,
        )
