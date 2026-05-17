from typing import Optional, List
from dataclasses import dataclass
from datetime import date as date_type

from app.database.repositories.contract import ContractRepository
from app.database.repositories.program import ProgramRepository
from app.database.models.contract import ExpertContract, ContractActivity
from app.services.program.service import normalize_program_code


@dataclass
class ContractData:
    """Data class for expert contract information."""

    id: int
    order_id: str
    dd: int
    mm: int
    yyyy: int
    abbreviated_project: str
    additional_information: Optional[str] = None
    total_amount: float = 0
    tax: float = 0.1
    final_amount: float = 0
    expert_id: int = 0
    program_id: int = 0

    # Denormalized program fields for convenience
    project_name: Optional[str] = None
    summary_activities: Optional[str] = None
    activity_purpose: Optional[str] = None
    start_date: Optional[date_type] = None
    end_date: Optional[date_type] = None


@dataclass
class ActivityData:
    """Data class for contract activity."""

    id: int
    activity_number: str
    activity_name: str
    budget: Optional[str] = None
    working_days: float = 0
    rate: float = 0
    real_amount: float = 0
    contract_id: int = 0


class ContractService:
    """Service for expert contract operations."""

    def __init__(
        self,
        contract_repository: ContractRepository,
        program_repository: Optional[ProgramRepository] = None,
    ):
        self._contract_repo = contract_repository
        self._program_repo = program_repository

    async def _validate_contract_date_range(self, data: ContractData) -> None:
        """Validate contract date against the program date range."""
        if self._program_repo is None or not data.program_id:
            return

        program = await self._program_repo.get_program_by_id(data.program_id)
        if program is None:
            return

        contract_date = date_type(data.yyyy, data.mm, data.dd)
        if program.start_date and contract_date < program.start_date:
            raise ValueError(
                "Ngày hợp đồng không được sớm hơn ngày bắt đầu dự án."
            )
        if program.end_date and contract_date > program.end_date:
            raise ValueError(
                "Ngày hợp đồng không được muộn hơn ngày kết thúc dự án."
            )

    async def resolve_program_code(self, program_code: str) -> Optional[int]:
        """Resolve a program_code to its program_id. Returns None if not found."""
        if self._program_repo is None:
            return None
        program = await self._program_repo.get_program_by_code(
            normalize_program_code(program_code)
        )
        return program.id if program else None

    async def create_contract(self, data: ContractData) -> ContractData:
        """Create a new contract (draft, before activities)."""
        existing = await self._contract_repo.get_contract_by_order_id_and_project(
            data.order_id,
            data.abbreviated_project,
        )
        if existing is not None:
            raise ValueError(
                "Số hợp đồng đã tồn tại trong cùng chương trình/dự án."
            )

        await self._validate_contract_date_range(data)

        contract = ExpertContract(
            order_id=data.order_id,
            dd=data.dd,
            mm=data.mm,
            yyyy=data.yyyy,
            abbreviated_project=data.abbreviated_project,
            additional_information=data.additional_information,
            total_amount=0,
            tax=data.tax,
            final_amount=0,
            expert_id=data.expert_id,
            program_id=data.program_id,
        )
        created = await self._contract_repo.create_contract(contract)
        return await self._to_contract_data(created)

    async def has_contract_order_in_project(
        self, order_id: str, abbreviated_project: str
    ) -> bool:
        """Check if same order id already exists in given project."""
        existing = await self._contract_repo.get_contract_by_order_id_and_project(
            order_id,
            abbreviated_project,
        )
        return existing is not None

    async def get_contract_by_id(self, contract_id: int) -> Optional[ContractData]:
        """Get a contract by ID."""
        contract = await self._contract_repo.get_contract_by_id(contract_id)
        if contract is None:
            return None
        return await self._to_contract_data(contract)

    async def get_contracts_by_expert_id(self, expert_id: int) -> List[ContractData]:
        """Get all contracts for an expert."""
        contracts = await self._contract_repo.get_contracts_by_expert_id(expert_id)
        return [await self._to_contract_data(c) for c in contracts]

    async def get_contracts_by_program_id(self, program_id: int) -> List[ContractData]:
        """Get all contracts for a program."""
        contracts = await self._contract_repo.get_contracts_by_program_id(program_id)
        return [await self._to_contract_data(c) for c in contracts]

    async def get_contracts_by_year(self, year: int) -> List[ContractData]:
        """Get all expert contracts in a year."""
        contracts = await self._contract_repo.get_contracts_by_year(year)
        return [await self._to_contract_data(c) for c in contracts]

    async def update_contract(
        self, contract_id: int, data: ContractData
    ) -> Optional[ContractData]:
        """Update a contract."""
        contract = await self._contract_repo.get_contract_by_id(contract_id)
        if contract is None:
            return None

        contract.order_id = data.order_id
        contract.dd = data.dd
        contract.mm = data.mm
        contract.yyyy = data.yyyy
        contract.abbreviated_project = data.abbreviated_project
        contract.additional_information = data.additional_information
        contract.total_amount = data.total_amount
        contract.tax = data.tax
        contract.final_amount = data.final_amount
        contract.program_id = data.program_id

        updated = await self._contract_repo.update_contract(contract)
        return await self._to_contract_data(updated)

    async def delete_contract(self, contract_id: int) -> bool:
        """Soft-delete a contract."""
        return await self._contract_repo.delete_contract(contract_id)

    async def add_activity(
        self, contract_id: int, data: ActivityData
    ) -> Optional[ActivityData]:
        """Add an activity to a contract."""
        existing = await self._contract_repo.get_activity_by_contract_and_number(
            contract_id,
            data.activity_number,
        )
        if existing is not None:
            raise ValueError("Hoạt động đã được lưu, không thể lưu trùng.")

        activity = ContractActivity(
            activity_number=data.activity_number,
            activity_name=data.activity_name,
            budget=data.budget,
            working_days=data.working_days,
            rate=data.rate,
            real_amount=data.real_amount,
            contract_id=contract_id,
        )
        created = await self._contract_repo.create_activity(activity)
        await self._contract_repo.recalculate_contract_totals(contract_id)
        return self._to_activity_data(created)

    async def get_activities_by_contract_id(
        self, contract_id: int
    ) -> List[ActivityData]:
        """Get all activities for a contract."""
        activities = await self._contract_repo.get_activities_by_contract_id(
            contract_id
        )
        return [self._to_activity_data(a) for a in activities]

    async def delete_activity(self, activity_id: int, contract_id: int) -> bool:
        """Delete an activity and recalculate totals."""
        success = await self._contract_repo.delete_activity(activity_id)
        if success:
            await self._contract_repo.recalculate_contract_totals(contract_id)
        return success

    async def finalize_contract(self, contract_id: int) -> Optional[ContractData]:
        """Finalize a contract by recalculating totals."""
        updated = await self._contract_repo.recalculate_contract_totals(contract_id)
        if updated is None:
            return None
        return await self._to_contract_data(updated)

    async def _to_contract_data(self, contract: ExpertContract) -> ContractData:
        """Convert ORM model to data class, denormalizing program fields."""
        # Resolve program fields via relationship if loaded, or query directly
        program = (
            contract.program
            if hasattr(contract, "program") and contract.program
            else None
        )

        return ContractData(
            id=contract.id,
            order_id=contract.order_id,
            dd=contract.dd,
            mm=contract.mm,
            yyyy=contract.yyyy,
            abbreviated_project=contract.abbreviated_project,
            additional_information=contract.additional_information,
            total_amount=contract.total_amount,
            tax=contract.tax,
            final_amount=contract.final_amount,
            expert_id=contract.expert_id,
            program_id=contract.program_id,
            project_name=program.name if program else None,
            summary_activities=program.summary_activities if program else None,
            activity_purpose=program.activity_purpose if program else None,
            start_date=program.start_date if program else None,
            end_date=program.end_date if program else None,
        )

    def _to_activity_data(self, activity: ContractActivity) -> ActivityData:
        """Convert ORM model to data class."""
        return ActivityData(
            id=activity.id,
            activity_number=activity.activity_number,
            activity_name=activity.activity_name,
            budget=activity.budget,
            working_days=activity.working_days,
            rate=activity.rate,
            real_amount=activity.real_amount,
            contract_id=activity.contract_id,
        )
