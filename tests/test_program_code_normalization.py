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
        ProgramData(id=0, program_code="proj-001", name="Test program")
    )
    assert created.program_code == "PROJ-001"


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
