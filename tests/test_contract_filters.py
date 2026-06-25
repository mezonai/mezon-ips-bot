from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.bot.handlers.expert import ExpertHandler
from app.services.bot.handlers.program import ProgramHandler
from app.services.contract.service import ContractData
from app.services.program.service import ProgramData


@pytest.mark.asyncio
async def test_program_command_accepts_direct_code(
    mock_client, mock_program_service, mock_contract_service
):
    program = ProgramData(id=1, program_code="PROJ-001", name="Project 1")
    mock_program_service.get_program_by_code = AsyncMock(return_value=program)

    handler = ProgramHandler(
        client=mock_client,
        program_service=mock_program_service,
        contract_service=mock_contract_service,
    )
    handler.reply_message = AsyncMock()

    await handler.handle_program(MagicMock(), "proj-001", None)

    mock_program_service.get_program_by_code.assert_awaited_once_with("PROJ-001")
    assert handler.reply_message.await_count == 1


@pytest.mark.asyncio
async def test_program_contract_list_button_filters_by_program(
    mock_client, mock_program_service, mock_contract_service
):
    mock_program_service.get_program_by_id = AsyncMock(
        return_value=ProgramData(id=1, program_code="PROJ-001", name="Project 1")
    )
    mock_contract_service.get_contracts_by_program_id = AsyncMock(
        return_value=[
            ContractData(
                id=2,
                order_id="HD-002",
                dd=2,
                mm=1,
                yyyy=2026,
                abbreviated_project="PROJ-001",
                expert_id=1,
                program_id=1,
            ),
            ContractData(
                id=1,
                order_id="HD-001",
                dd=1,
                mm=1,
                yyyy=2026,
                abbreviated_project="PROJ-001",
                expert_id=2,
                program_id=1,
            ),
        ]
    )
    mock_contract_service.get_activities_by_contract_id = AsyncMock(return_value=[])

    handler = ProgramHandler(
        client=mock_client,
        program_service=mock_program_service,
        contract_service=mock_contract_service,
    )
    handler.edit_message = AsyncMock()

    await handler._handle_view_program_contracts(
        MagicMock(channel_id=1, message_id=2), 1
    )

    mock_contract_service.get_contracts_by_program_id.assert_awaited_once_with(1)
    assert "HD-002" in handler.edit_message.call_args[0][2]


@pytest.mark.asyncio
async def test_contract_command_lists_expert_contracts_by_year(
    mock_client,
    mock_contract_service,
    mock_expert_service,
    mock_program_service,
    mock_word_export_service,
):
    mock_contract_service.get_contracts_by_year = AsyncMock(
        return_value=[
            ContractData(
                id=2,
                order_id="HD-002",
                dd=2,
                mm=1,
                yyyy=2026,
                abbreviated_project="PROJ-002",
                project_name="Project 2",
                expert_id=2,
                program_id=2,
                total_amount=2000,
                final_amount=1800,
            ),
            ContractData(
                id=1,
                order_id="HD-001",
                dd=1,
                mm=1,
                yyyy=2026,
                abbreviated_project="PROJ-001",
                project_name="Project 1",
                expert_id=1,
                program_id=1,
                total_amount=1000,
                final_amount=900,
            ),
        ]
    )
    mock_contract_service.get_activities_by_contract_id = AsyncMock(return_value=[])
    mock_expert_service.get_expert_by_id = AsyncMock(
        side_effect=[
            MagicMock(pronoun="Ông", expert_name="B"),
            MagicMock(pronoun="Bà", expert_name="A"),
        ]
    )

    handler = ExpertHandler(
        client=mock_client,
        expert_service=mock_expert_service,
        contract_service=mock_contract_service,
        program_service=mock_program_service,
        word_export_service=mock_word_export_service,
        smb_upload_service=None,
    )
    handler.reply_message = AsyncMock()

    await handler.handle_contract(MagicMock(), "expert", "list", "year", "2026")

    mock_contract_service.get_contracts_by_year.assert_awaited_once_with(2026)
    text = handler.reply_message.call_args[0][1]
    assert "HD-002" in text
    assert text.index("HD-002") < text.index("HD-001")


@pytest.mark.asyncio
async def test_contract_command_without_args_shows_help(
    mock_client,
    mock_contract_service,
    mock_expert_service,
    mock_program_service,
    mock_word_export_service,
):
    handler = ExpertHandler(
        client=mock_client,
        expert_service=mock_expert_service,
        contract_service=mock_contract_service,
        program_service=mock_program_service,
        word_export_service=mock_word_export_service,
        smb_upload_service=None,
    )
    handler.reply_message = AsyncMock()

    await handler.handle_contract(MagicMock())

    handler.reply_message.assert_awaited_once()
    text = handler.reply_message.await_args.args[1]
    assert "Quản lý hợp đồng" in text
    assert "`*contract expert list year <YYYY>`" in text
