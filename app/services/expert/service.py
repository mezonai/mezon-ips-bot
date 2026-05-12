from typing import Optional, List
from dataclasses import dataclass
from datetime import date

from app.database.repositories.expert import ExpertRepository
from app.database.models.expert import Expert


@dataclass
class ExpertData:
    """Data class for expert information."""

    id: int
    pronoun: str
    expert_name: str
    nationality: Optional[str] = None
    address: Optional[str] = None
    id_number: Optional[str] = None
    issued_date: Optional[date] = None
    issued_place: Optional[str] = None
    email_address: Optional[str] = None
    phone: Optional[str] = None
    bank_account: Optional[str] = None
    bank_name: Optional[str] = None


class ExpertService:
    """Service for expert operations."""

    def __init__(self, expert_repository: ExpertRepository):
        self._repository = expert_repository

    async def create_expert(self, data: ExpertData) -> ExpertData:
        """Create a new expert record."""
        expert = Expert(
            pronoun=data.pronoun,
            expert_name=data.expert_name,
            nationality=data.nationality,
            address=data.address,
            id_number=data.id_number,
            issued_date=data.issued_date,
            issued_place=data.issued_place,
            email_address=data.email_address,
            phone=data.phone,
            bank_account=data.bank_account,
            bank_name=data.bank_name,
        )
        created = await self._repository.create(expert)
        return self._to_data(created)

    async def get_expert_by_id(self, expert_id: int) -> Optional[ExpertData]:
        """Get an expert by ID."""
        expert = await self._repository.get_by_id(expert_id)
        if expert is None:
            return None
        return self._to_data(expert)

    async def get_active_expert_by_id(self, expert_id: int) -> Optional[ExpertData]:
        """Get an active expert by ID."""
        expert = await self._repository.get_active_by_id(expert_id)
        if expert is None:
            return None
        return self._to_data(expert)

    async def find_by_name(self, name: str) -> List[ExpertData]:
        """Find experts by name (case-insensitive partial match)."""
        experts = await self._repository.find_by_name(name)
        return [self._to_data(p) for p in experts]

    async def find_by_id_number(self, id_number: str) -> Optional[ExpertData]:
        """Find an expert by CCCD/id_number."""
        expert = await self._repository.find_by_id_number(id_number)
        if expert is None:
            return None
        return self._to_data(expert)

    async def resolve_experts(self, keyword: str) -> List[ExpertData]:
        """Resolve user input to experts by CCCD first, then by name."""
        normalized = keyword.strip()
        if not normalized:
            return []

        exact_match = await self.find_by_id_number(normalized)
        if exact_match is not None:
            return [exact_match]

        return await self.find_by_name(normalized)

    async def update_expert(
        self, expert_id: int, data: ExpertData
    ) -> Optional[ExpertData]:
        """Update an expert's information."""
        expert = await self._repository.get_by_id(expert_id)
        if expert is None:
            return None

        expert.pronoun = data.pronoun
        expert.expert_name = data.expert_name
        expert.nationality = data.nationality
        expert.address = data.address
        expert.id_number = data.id_number
        expert.issued_date = data.issued_date
        expert.issued_place = data.issued_place
        expert.email_address = data.email_address
        expert.phone = data.phone
        expert.bank_account = data.bank_account
        expert.bank_name = data.bank_name

        updated = await self._repository.update(expert)
        return self._to_data(updated)

    async def delete_expert(self, expert_id: int) -> bool:
        """Soft-delete an expert."""
        return await self._repository.delete(expert_id)

    async def list_all(self, limit: int = 50) -> List[ExpertData]:
        """List all experts."""
        experts = await self._repository.list_all(limit=limit)
        return [self._to_data(p) for p in experts]

    def _to_data(self, expert: Expert) -> ExpertData:
        """Convert ORM model to data class."""
        return ExpertData(
            id=expert.id,
            pronoun=expert.pronoun,
            expert_name=expert.expert_name,
            nationality=expert.nationality,
            address=expert.address,
            id_number=expert.id_number,
            issued_date=expert.issued_date,
            issued_place=expert.issued_place,
            email_address=expert.email_address,
            phone=expert.phone,
            bank_account=expert.bank_account,
            bank_name=expert.bank_name,
        )
