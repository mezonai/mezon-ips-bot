from typing import Optional, List

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database.repositories.base import BaseRepository
from app.database.models.contract import ExpertContract, ContractActivity


class ContractRepository(BaseRepository):
    """Repository for expert contract data access."""

    async def create_contract(self, contract: ExpertContract) -> ExpertContract:
        """Create a new expert contract."""
        async with self._get_session() as session:
            session.add(contract)
            await session.commit()
            await session.refresh(contract, ["program"])
            return contract

    async def get_contract_by_order_id_and_project(
        self, order_id: str, abbreviated_project: str
    ) -> Optional[ExpertContract]:
        """Get non-deleted contract by order id within same project."""
        async with self._get_session() as session:
            result = await session.execute(
                select(ExpertContract).where(
                    ExpertContract.order_id == order_id,
                    ExpertContract.abbreviated_project == abbreviated_project,
                    ExpertContract.deleted_at.is_(None),
                )
            )
            return result.scalars().first()

    async def get_contract_by_unique_attrs(
        self, yyyy: int, abbreviated_project: str, additional_information: Optional[str]
    ) -> Optional[ExpertContract]:
        """Get non-deleted contract by yyyy, abbreviated_project, and additional_information."""
        async with self._get_session() as session:
            query = select(ExpertContract).where(
                ExpertContract.yyyy == yyyy,
                ExpertContract.abbreviated_project == abbreviated_project,
                ExpertContract.deleted_at.is_(None),
            )
            if additional_information is None:
                query = query.where(ExpertContract.additional_information.is_(None))
            else:
                query = query.where(ExpertContract.additional_information == additional_information)

            result = await session.execute(query)
            return result.scalars().first()

    async def get_contract_by_id(self, contract_id: int) -> Optional[ExpertContract]:
        """Get contract by ID with activities and program."""
        async with self._get_session() as session:
            result = await session.execute(
                select(ExpertContract)
                .options(selectinload(ExpertContract.program), selectinload(ExpertContract.activities))
                .where(ExpertContract.id == contract_id)
            )
            return result.scalars().first()

    async def get_contracts_by_expert_id(
        self, expert_id: int
    ) -> List[ExpertContract]:
        """Get all contracts for an expert."""
        async with self._get_session() as session:
            result = await session.execute(
                select(ExpertContract)
                .options(selectinload(ExpertContract.program))
                .where(
                    ExpertContract.expert_id == expert_id,
                    ExpertContract.deleted_at.is_(None),
                )
                .order_by(ExpertContract.created_at.desc())
            )
            contracts = result.scalars().all()
            for contract in contracts:
                await session.refresh(contract, ["activities"])
            return contracts

    async def get_contracts_by_program_id(
        self, program_id: int
    ) -> List[ExpertContract]:
        """Get all contracts for a program, newest contract date first."""
        async with self._get_session() as session:
            result = await session.execute(
                select(ExpertContract)
                .options(selectinload(ExpertContract.program))
                .where(
                    ExpertContract.program_id == program_id,
                    ExpertContract.deleted_at.is_(None),
                )
                .order_by(
                    ExpertContract.yyyy.desc(),
                    ExpertContract.mm.desc(),
                    ExpertContract.dd.desc(),
                    ExpertContract.created_at.desc(),
                )
            )
            contracts = result.scalars().all()
            for contract in contracts:
                await session.refresh(contract, ["activities"])
            return contracts

    async def get_contracts_by_year(self, year: int) -> List[ExpertContract]:
        """Get all contracts in a year, newest contract date first."""
        async with self._get_session() as session:
            result = await session.execute(
                select(ExpertContract)
                .options(selectinload(ExpertContract.program))
                .where(
                    ExpertContract.yyyy == year,
                    ExpertContract.deleted_at.is_(None),
                )
                .order_by(
                    ExpertContract.yyyy.desc(),
                    ExpertContract.mm.desc(),
                    ExpertContract.dd.desc(),
                    ExpertContract.created_at.desc(),
                )
            )
            contracts = result.scalars().all()
            for contract in contracts:
                await session.refresh(contract, ["activities"])
            return contracts

    async def update_contract(self, contract: ExpertContract) -> ExpertContract:
        """Update an existing contract."""
        async with self._get_session() as session:
            session.add(contract)
            await session.commit()
            await session.refresh(contract, ["program"])
            return contract

    async def delete_contract(self, contract_id: int) -> bool:
        """Soft-delete a contract."""
        from datetime import datetime, timezone

        async with self._get_session() as session:
            result = await session.execute(
                select(ExpertContract).where(ExpertContract.id == contract_id)
            )
            contract = result.scalars().first()
            if contract:
                contract.deleted_at = datetime.now(timezone.utc)
                await session.commit()
                return True
            return False

    async def create_activity(self, activity: ContractActivity) -> ContractActivity:
        """Create a new contract activity."""
        async with self._get_session() as session:
            session.add(activity)
            await session.commit()
            await session.refresh(activity)
            return activity

    async def get_activity_by_contract_and_number(
        self, contract_id: int, activity_number: str
    ) -> Optional[ContractActivity]:
        """Get non-deleted activity by contract and activity number."""
        async with self._get_session() as session:
            result = await session.execute(
                select(ContractActivity).where(
                    ContractActivity.contract_id == contract_id,
                    ContractActivity.activity_number == activity_number,
                    ContractActivity.deleted_at.is_(None),
                )
            )
            return result.scalars().first()

    async def get_activities_by_contract_id(
        self, contract_id: int
    ) -> List[ContractActivity]:
        """Get all activities for a contract."""
        async with self._get_session() as session:
            result = await session.execute(
                select(ContractActivity)
                .where(
                    ContractActivity.contract_id == contract_id,
                    ContractActivity.deleted_at.is_(None),
                )
                .order_by(ContractActivity.activity_number)
            )
            return result.scalars().all()

    async def delete_activity(self, activity_id: int) -> bool:
        """Soft-delete an activity."""
        from datetime import datetime, timezone

        async with self._get_session() as session:
            result = await session.execute(
                select(ContractActivity).where(ContractActivity.id == activity_id)
            )
            activity = result.scalars().first()
            if activity:
                activity.deleted_at = datetime.now(timezone.utc)
                await session.commit()
                return True
            return False

    async def recalculate_contract_totals(self, contract_id: int) -> Optional[ExpertContract]:
        """Recalculate total_amount, tax, and final_amount based on activities."""
        async with self._get_session() as session:
            result = await session.execute(
                select(ExpertContract)
                .options(selectinload(ExpertContract.program))
                .where(ExpertContract.id == contract_id)
            )
            contract = result.scalars().first()
            if not contract:
                return None

            activities_result = await session.execute(
                select(ContractActivity).where(
                    ContractActivity.contract_id == contract_id,
                    ContractActivity.deleted_at.is_(None),
                )
            )
            activities = activities_result.scalars().all()
            contract.total_amount = sum(a.real_amount for a in activities)
            contract.final_amount = contract.total_amount * (1 - contract.tax)
            await session.commit()
            await session.refresh(contract, ["program"])
            return contract
