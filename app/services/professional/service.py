from typing import Optional, List
from dataclasses import dataclass
from datetime import date

from app.database.repositories.professional import ProfessionalRepository
from app.database.models.professional import Professional


@dataclass
class ProfessionalData:
    """Data class for professional information."""

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
    rate: Optional[float] = None


class ProfessionalService:
    """Service for professional (expert) operations."""

    def __init__(self, professional_repository: ProfessionalRepository):
        self._repository = professional_repository

    async def create_professional(self, data: ProfessionalData) -> ProfessionalData:
        """Create a new professional record."""
        professional = Professional(
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
            rate=data.rate,
        )
        created = await self._repository.create(professional)
        return self._to_data(created)

    async def get_professional_by_id(
        self, professional_id: int
    ) -> Optional[ProfessionalData]:
        """Get a professional by ID."""
        professional = await self._repository.get_by_id(professional_id)
        if professional is None:
            return None
        return self._to_data(professional)

    async def find_by_name(self, name: str) -> List[ProfessionalData]:
        """Find professionals by name (case-insensitive partial match)."""
        professionals = await self._repository.find_by_name(name)
        return [self._to_data(p) for p in professionals]

    async def find_by_id_number(self, id_number: str) -> Optional[ProfessionalData]:
        """Find a professional by CCCD/id_number."""
        professional = await self._repository.find_by_id_number(id_number)
        if professional is None:
            return None
        return self._to_data(professional)

    async def update_professional(
        self, professional_id: int, data: ProfessionalData
    ) -> Optional[ProfessionalData]:
        """Update a professional's information."""
        professional = await self._repository.get_by_id(professional_id)
        if professional is None:
            return None

        professional.pronoun = data.pronoun
        professional.expert_name = data.expert_name
        professional.nationality = data.nationality
        professional.address = data.address
        professional.id_number = data.id_number
        professional.issued_date = data.issued_date
        professional.issued_place = data.issued_place
        professional.email_address = data.email_address
        professional.phone = data.phone
        professional.bank_account = data.bank_account
        professional.bank_name = data.bank_name
        professional.rate = data.rate

        updated = await self._repository.update(professional)
        return self._to_data(updated)

    async def delete_professional(self, professional_id: int) -> bool:
        """Soft-delete a professional."""
        return await self._repository.delete(professional_id)

    async def list_all(self, limit: int = 50) -> List[ProfessionalData]:
        """List all professionals."""
        professionals = await self._repository.list_all(limit=limit)
        return [self._to_data(p) for p in professionals]

    def _to_data(self, professional: Professional) -> ProfessionalData:
        """Convert ORM model to data class."""
        return ProfessionalData(
            id=professional.id,
            pronoun=professional.pronoun,
            expert_name=professional.expert_name,
            nationality=professional.nationality,
            address=professional.address,
            id_number=professional.id_number,
            issued_date=professional.issued_date,
            issued_place=professional.issued_place,
            email_address=professional.email_address,
            phone=professional.phone,
            bank_account=professional.bank_account,
            bank_name=professional.bank_name,
            rate=professional.rate,
        )
