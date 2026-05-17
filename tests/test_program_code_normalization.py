from datetime import date
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.bot.handlers.program import ProgramHandler
from app.services.contract.service import ContractService
from app.services.program.service import ProgramData, ProgramService


@pytest.mark.asyncio
async def test_program_service_normalizes_code_for_lookup_and_storage():
    repository = MagicMock()
    repository.get_program_by_code = AsyncMock(return_value=None)
    repository.create_program = AsyncMock(side_effect=lambda program: program)

    service = ProgramService(repository)

    await service.get_program_by_code("proj-001")
    repository.get_program_by_code.assert_awaited_once_with("PROJ-001")

    created = await service.create_program(
        ProgramData(
            id=0,
            program_code="proj-001",
            name="Test program",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
        )
    )
    assert created.program_code == "PROJ-001"
    assert created.start_date == date(2026, 1, 1)


@pytest.mark.asyncio
async def test_program_service_rejects_start_date_after_end_date():
    repository = MagicMock()
    service = ProgramService(repository)

    with pytest.raises(ValueError, match="Ngày bắt đầu dự án không được muộn hơn ngày kết thúc dự án"):
        await service.create_program(
            ProgramData(
                id=0,
                program_code="PROJ-001",
                name="Test program",
                start_date=date(2026, 12, 31),
                end_date=date(2026, 1, 1),
            )
        )


@pytest.mark.asyncio
async def test_program_service_updates_start_and_end_dates():
    repository = MagicMock()
    existing = MagicMock(
        id=1,
        program_code="OLD-001",
        name="Old program",
        summary_activities=None,
        activity_purpose=None,
        start_date=None,
        end_date=None,
    )
    repository.get_program_by_id = AsyncMock(return_value=existing)
    repository.update_program = AsyncMock(side_effect=lambda program: program)
    service = ProgramService(repository)

    updated = await service.update_program(
        1,
        ProgramData(
            id=1,
            program_code="proj-001",
            name="Updated program",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
        ),
    )

    assert updated is not None
    assert updated.program_code == "PROJ-001"
    assert updated.start_date == date(2026, 1, 1)
    assert updated.end_date == date(2026, 12, 31)


@pytest.mark.asyncio
async def test_program_service_rejects_invalid_date_range_on_update():
    repository = MagicMock()
    service = ProgramService(repository)

    with pytest.raises(ValueError, match="Ngày bắt đầu dự án không được muộn hơn ngày kết thúc dự án"):
        await service.update_program(
            1,
            ProgramData(
                id=1,
                program_code="PROJ-001",
                name="Updated program",
                start_date=date(2026, 12, 31),
                end_date=date(2026, 1, 1),
            ),
        )


@pytest.mark.asyncio
async def test_contract_service_resolves_program_code_case_insensitively():
    repository = MagicMock()
    repository.get_program_by_code = AsyncMock(return_value=MagicMock(id=7))

    service = ContractService(MagicMock(), repository)

    program_id = await service.resolve_program_code("proj-002")

    assert program_id == 7
    repository.get_program_by_code.assert_awaited_once_with("PROJ-002")


@pytest.mark.asyncio
async def test_program_handler_find_normalizes_search_code(mock_client):
    program_service = MagicMock()
    program_service.get_program_by_code = AsyncMock(
        return_value=ProgramData(id=1, program_code="PROJ-003", name="Program 3")
    )
    handler = ProgramHandler(client=mock_client, program_service=program_service)
    handler.reply_message = AsyncMock()

    await handler._handle_find(MagicMock(), "proj-003")

    program_service.get_program_by_code.assert_awaited_once_with("PROJ-003")
    assert handler.reply_message.await_count == 1
