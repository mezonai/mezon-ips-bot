from datetime import date
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.bot.handlers.expert import ExpertHandler
from app.services.expert.service import ExpertData, ExpertService


@pytest.mark.asyncio
async def test_expert_service_rejects_duplicate_id_number_on_create():
    repository = MagicMock()
    repository.find_by_id_number = AsyncMock(
        return_value=MagicMock(
            id=1,
            pronoun="Ông",
            expert_name="Existing Expert",
            id_number="012345678901",
            nationality=None,
            address=None,
            issued_date=None,
            issued_place=None,
            email_address=None,
            phone=None,
            bank_account=None,
            bank_name=None,
        )
    )
    service = ExpertService(repository)

    with pytest.raises(ValueError, match="CCCD `012345678901` đã tồn tại"):
        await service.create_expert(
            ExpertData(
                id=0,
                pronoun="Ông",
                expert_name="New Expert",
                id_number="012345678901",
            )
        )


@pytest.mark.asyncio
async def test_expert_service_rejects_duplicate_id_number_on_update():
    repository = MagicMock()
    repository.get_by_id = AsyncMock(
        return_value=MagicMock(
            id=2,
            pronoun="Ông",
            expert_name="Current Expert",
            id_number="099999999999",
            nationality=None,
            address=None,
            issued_date=None,
            issued_place=None,
            email_address=None,
            phone=None,
            bank_account=None,
            bank_name=None,
        )
    )
    repository.find_by_id_number = AsyncMock(
        return_value=MagicMock(
            id=1,
            pronoun="Bà",
            expert_name="Existing Expert",
            id_number="012345678901",
            nationality=None,
            address=None,
            issued_date=None,
            issued_place=None,
            email_address=None,
            phone=None,
            bank_account=None,
            bank_name=None,
        )
    )
    service = ExpertService(repository)

    with pytest.raises(ValueError, match="CCCD `012345678901` đã tồn tại"):
        await service.update_expert(
            2,
            ExpertData(
                id=2,
                pronoun="Ông",
                expert_name="Current Expert",
                id_number="012345678901",
            ),
        )


@pytest.mark.asyncio
async def test_expert_handler_ignores_duplicate_save_submit_from_same_message(
    mock_client,
    mock_expert_service,
):
    handler = ExpertHandler(
        client=mock_client,
        expert_service=mock_expert_service,
        contract_service=None,
        program_service=None,
        word_export_service=None,
        smb_upload_service=None,
    )
    handler.edit_message = AsyncMock()
    mock_expert_service.create_expert = AsyncMock(
        return_value=ExpertData(
            id=1,
            pronoun="Ông",
            expert_name="Nguyen Van A",
            id_number="012345678901",
            issued_date=date(2020, 1, 1),
        )
    )

    event = MagicMock(channel_id=1, message_id=99)
    extra_data = {
        "expert_name": "Nguyen Van A",
        "pronoun": "Ông",
        "id_number": "012345678901",
    }

    await handler._handle_save(event, extra_data)
    await handler._handle_save(event, extra_data)

    mock_expert_service.create_expert.assert_awaited_once()
    assert "đã được lưu trước đó" in handler.edit_message.await_args_list[-1].args[2]
