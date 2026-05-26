from datetime import date
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.bot.handlers.expert import ExpertHandler
from app.services.contract.service import ContractData, ContractService


@pytest.mark.asyncio
async def test_contract_service_rejects_duplicate_order_id_in_same_project():
    repository = MagicMock()
    repository.get_contract_by_order_id_and_project = AsyncMock(return_value=MagicMock())

    service = ContractService(repository, MagicMock())

    with pytest.raises(ValueError, match="Số hợp đồng đã tồn tại"):
        await service.create_contract(
            ContractData(
                id=0,
                order_id="HD-001",
                dd=1,
                mm=1,
                yyyy=2026,
                abbreviated_project="PROJ-001",
                expert_id=1,
                program_id=1,
            )
        )


@pytest.mark.asyncio
async def test_contract_service_rejects_contract_date_before_program_start():
    contract_repository = MagicMock()
    contract_repository.get_contract_by_order_id_and_project = AsyncMock(return_value=None)
    program_repository = MagicMock()
    program_repository.get_program_by_id = AsyncMock(
        return_value=MagicMock(start_date=date(2026, 2, 1), end_date=date(2026, 12, 31))
    )

    service = ContractService(contract_repository, program_repository)

    with pytest.raises(
        ValueError,
        match="Ngày hợp đồng không được sớm hơn ngày bắt đầu dự án",
    ):
        await service.create_contract(
            ContractData(
                id=0,
                order_id="HD-001",
                dd=1,
                mm=1,
                yyyy=2026,
                abbreviated_project="PROJ-001",
                expert_id=1,
                program_id=1,
            )
        )


@pytest.mark.asyncio
async def test_contract_service_rejects_contract_date_after_program_end():
    contract_repository = MagicMock()
    contract_repository.get_contract_by_order_id_and_project = AsyncMock(return_value=None)
    program_repository = MagicMock()
    program_repository.get_program_by_id = AsyncMock(
        return_value=MagicMock(start_date=date(2026, 1, 1), end_date=date(2026, 3, 31))
    )

    service = ContractService(contract_repository, program_repository)

    with pytest.raises(
        ValueError,
        match="Ngày hợp đồng không được muộn hơn ngày kết thúc dự án",
    ):
        await service.create_contract(
            ContractData(
                id=0,
                order_id="HD-001",
                dd=1,
                mm=4,
                yyyy=2026,
                abbreviated_project="PROJ-001",
                expert_id=1,
                program_id=1,
            )
        )


@pytest.mark.asyncio
async def test_contract_service_allows_contract_date_within_program_range():
    contract_repository = MagicMock()
    contract_repository.get_contract_by_order_id_and_project = AsyncMock(return_value=None)
    contract_repository.create_contract = AsyncMock(side_effect=lambda contract: contract)
    program_repository = MagicMock()
    program_repository.get_program_by_id = AsyncMock(
        return_value=MagicMock(
            id=1,
            name="Program 1",
            summary_activities="Summary",
            activity_purpose="Purpose",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
        )
    )

    service = ContractService(contract_repository, program_repository)

    created = await service.create_contract(
        ContractData(
            id=0,
            order_id="HD-001",
            dd=15,
            mm=6,
            yyyy=2026,
            abbreviated_project="PROJ-001",
            expert_id=1,
            program_id=1,
        )
    )

    assert created.order_id == "HD-001"
    contract_repository.create_contract.assert_awaited_once()


@pytest.mark.asyncio
async def test_contract_service_rejects_duplicate_unique_attrs():
    contract_repository = MagicMock()
    contract_repository.get_contract_by_order_id_and_project = AsyncMock(return_value=None)
    contract_repository.get_contract_by_unique_attrs = AsyncMock(return_value=MagicMock())
    program_repository = MagicMock()

    service = ContractService(contract_repository, program_repository)

    with pytest.raises(
        ValueError,
        match="Hợp đồng có cùng năm, dự án và thông tin thêm đã tồn tại",
    ):
        await service.create_contract(
            ContractData(
                id=0,
                order_id="HD-001",
                dd=15,
                mm=6,
                yyyy=2026,
                abbreviated_project="PROJ-001",
                additional_information="Some Info",
                expert_id=1,
                program_id=1,
            )
        )


@pytest.mark.asyncio
async def test_acceptance_export_blocked_when_today_exceeds_contract_end_date(
    mock_client,
    mock_expert_service,
    mock_program_service,
    mock_word_export_service,
):
    contract_service = MagicMock()
    contract_service.get_contract_by_id = AsyncMock(
        return_value=ContractData(
            id=1,
            order_id="HD-001",
            dd=1,
            mm=1,
            yyyy=2026,
            abbreviated_project="PROJ-001",
            expert_id=1,
            program_id=1,
            end_date=date(2024, 1, 1),
        )
    )

    handler = ExpertHandler(
        client=mock_client,
        expert_service=mock_expert_service,
        contract_service=contract_service,
        program_service=mock_program_service,
        word_export_service=mock_word_export_service,
        s3_upload_service=None,
    )
    handler.edit_message = AsyncMock()

    await handler._export_acceptance_direct(MagicMock(channel_id=1, message_id=2), 1, [])

    assert "vượt quá ngày kết thúc hợp đồng" in handler.edit_message.call_args[0][2]
