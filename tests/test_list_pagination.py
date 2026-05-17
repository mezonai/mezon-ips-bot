from datetime import date
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.bot.handlers.expert import ExpertHandler
from app.services.bot.handlers.program import ProgramHandler
from app.services.contract.service import ContractData
from app.services.expert.service import ExpertData
from app.services.program.service import ProgramData


def _embed_dump(embed):
    if hasattr(embed, "model_dump"):
        return embed.model_dump()
    if hasattr(embed, "dict"):
        return embed.dict()
    return embed


@pytest.mark.asyncio
async def test_expert_list_paginates_with_next_button(
    mock_client, mock_expert_service, mock_program_service, mock_word_export_service
):
    mock_expert_service.list_all = AsyncMock(
        return_value=[
            ExpertData(id=i, pronoun="Ông", expert_name=f"Expert {i}", id_number=f"{i:012d}")
            for i in range(1, 12)
        ]
    )
    handler = ExpertHandler(
        client=mock_client,
        expert_service=mock_expert_service,
        contract_service=MagicMock(),
        program_service=mock_program_service,
        word_export_service=mock_word_export_service,
        s3_upload_service=None,
    )
    handler.reply_message = AsyncMock()

    await handler._handle_list(MagicMock())

    text = handler.reply_message.await_args.args[1]
    components = handler.reply_message.await_args.kwargs["components"]
    embed = _embed_dump(handler.reply_message.await_args.kwargs["embeds"][0])

    assert "Trang 1/2" in text
    assert "Expert 11" not in str(embed)
    component_ids = [c.component_id for row in components for c in row.components]
    assert "expert_list_page:2" in component_ids


@pytest.mark.asyncio
async def test_expert_contract_list_paginates_from_detail_button(
    mock_client, mock_contract_service, mock_expert_service, mock_program_service, mock_word_export_service
):
    mock_contract_service.get_contracts_by_expert_id = AsyncMock(
        return_value=[
            ContractData(
                id=i,
                order_id=f"HD-{i:03d}",
                dd=1,
                mm=1,
                yyyy=2026,
                abbreviated_project=f"PROJ-{i:03d}",
                project_name=f"Project {i}",
                expert_id=1,
                program_id=1,
            )
            for i in range(1, 12)
        ]
    )
    mock_contract_service.get_activities_by_contract_id = AsyncMock(return_value=[])
    mock_expert_service.get_expert_by_id = AsyncMock(
        return_value=ExpertData(id=1, pronoun="Ông", expert_name="Expert 1")
    )
    handler = ExpertHandler(
        client=mock_client,
        expert_service=mock_expert_service,
        contract_service=mock_contract_service,
        program_service=mock_program_service,
        word_export_service=mock_word_export_service,
        s3_upload_service=None,
    )
    handler.edit_message = AsyncMock()

    await handler._handle_list_contracts_button(
        MagicMock(channel_id=1, message_id=2), 1, page=2
    )

    text = handler.edit_message.call_args.args[2]
    components = handler.edit_message.call_args.kwargs["components"]
    component_ids = [c.component_id for row in components for c in row.components]

    assert "Trang 2/2" in text
    assert "HD-011" in text
    assert "HD-001" not in text
    assert "expert_contracts_page:1:1" in component_ids


@pytest.mark.asyncio
async def test_contract_year_list_paginates_with_buttons(
    mock_client, mock_contract_service, mock_expert_service, mock_program_service, mock_word_export_service
):
    mock_contract_service.get_contracts_by_year = AsyncMock(
        return_value=[
            ContractData(
                id=i,
                order_id=f"HD-{i:03d}",
                dd=1,
                mm=1,
                yyyy=2026,
                abbreviated_project=f"PROJ-{i:03d}",
                project_name=f"Project {i}",
                expert_id=1,
                program_id=1,
            )
            for i in range(1, 12)
        ]
    )
    mock_contract_service.get_activities_by_contract_id = AsyncMock(return_value=[])
    mock_expert_service.get_expert_by_id = AsyncMock(
        return_value=ExpertData(id=1, pronoun="Ông", expert_name="Expert 1")
    )
    handler = ExpertHandler(
        client=mock_client,
        expert_service=mock_expert_service,
        contract_service=mock_contract_service,
        program_service=mock_program_service,
        word_export_service=mock_word_export_service,
        s3_upload_service=None,
    )
    handler.reply_message = AsyncMock()
    handler.edit_message = AsyncMock()

    await handler.handle_contract(MagicMock(), "expert", "list", "year", "2026")
    first_components = handler.reply_message.await_args.kwargs["components"]
    first_ids = [c.component_id for row in first_components for c in row.components]
    assert "contract_year_page:2026:2" in first_ids

    await handler.handle_button_click(
        MagicMock(
            button_id="contract_year_page:2026:2",
            channel_id=1,
            message_id=2,
            extra_data="",
        )
    )
    edited_text = handler.edit_message.call_args.args[2]
    assert "Trang 2/2" in edited_text
    assert "HD-011" in edited_text
    assert "HD-001" not in edited_text


@pytest.mark.asyncio
async def test_program_list_paginates_with_next_button(
    mock_client, mock_program_service, mock_contract_service
):
    mock_program_service.list_programs = AsyncMock(
        return_value=[
            ProgramData(
                id=i,
                program_code=f"PROJ-{i:03d}",
                name=f"Program {i}",
                start_date=date(2026, 1, 1),
                end_date=date(2026, 12, 31),
            )
            for i in range(1, 12)
        ]
    )
    handler = ProgramHandler(
        client=mock_client,
        program_service=mock_program_service,
        contract_service=mock_contract_service,
    )
    handler.reply_message = AsyncMock()

    await handler._handle_list(MagicMock())

    text = handler.reply_message.await_args.args[1]
    components = handler.reply_message.await_args.kwargs["components"]
    component_ids = [c.component_id for row in components for c in row.components]

    assert "Trang 1/2" in text
    assert "PROJ-011" not in text
    assert "program_list_page:2" in component_ids


@pytest.mark.asyncio
async def test_program_contract_list_paginates_from_detail_button(
    mock_client, mock_program_service, mock_contract_service
):
    mock_program_service.get_program_by_id = AsyncMock(
        return_value=ProgramData(id=1, program_code="PROJ-001", name="Program 1")
    )
    mock_contract_service.get_contracts_by_program_id = AsyncMock(
        return_value=[
            ContractData(
                id=i,
                order_id=f"HD-{i:03d}",
                dd=1,
                mm=1,
                yyyy=2026,
                abbreviated_project="PROJ-001",
                expert_id=1,
                program_id=1,
            )
            for i in range(1, 12)
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
        MagicMock(channel_id=1, message_id=2), 1, page=2
    )

    text = handler.edit_message.call_args.args[2]
    components = handler.edit_message.call_args.kwargs["components"]
    component_ids = [c.component_id for row in components for c in row.components]

    assert "Trang 2/2" in text
    assert "HD-011" in text
    assert "HD-001" not in text
    assert "program_contracts_page:1:1" in component_ids
