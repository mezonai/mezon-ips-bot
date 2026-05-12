from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.contract.service import ActivityData, ContractService


@pytest.mark.asyncio
async def test_contract_service_rejects_duplicate_activity_number():
    repository = MagicMock()
    repository.get_activity_by_contract_and_number = AsyncMock(return_value=MagicMock())
    service = ContractService(repository, MagicMock())

    with pytest.raises(ValueError, match="Hoạt động đã được lưu"):
        await service.add_activity(
            1,
            ActivityData(
                id=0,
                activity_number="01",
                activity_name="Review",
                working_days=4.5,
                rate=2000000,
                real_amount=9000000,
                contract_id=1,
            ),
        )
