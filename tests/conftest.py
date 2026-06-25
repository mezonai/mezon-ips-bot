"""Shared test fixtures for acceptance report tests."""

import os
import tempfile
from datetime import date
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.contract.service import ContractData, ActivityData
from app.services.expert.service import ExpertData


@pytest.fixture
def mock_expert():
    """Create a mock ExpertData instance."""
    return ExpertData(
        id=1,
        pronoun="Ông",
        expert_name="Nguyen Van A",
        nationality="Viet Nam",
        address="123 Test Street, Hanoi",
        id_number="012345678901",
        issued_date=date(2020, 1, 15),
        issued_place="Cuc CSQLHC ve TTXH",
        email_address="test@example.com",
        phone="0912345678",
        bank_account="1234567890",
        bank_name="Vietcombank",
    )


@pytest.fixture
def mock_contract():
    """Create a mock ContractData instance."""
    return ContractData(
        id=1,
        order_id="HDCG-2024-001",
        dd=1,
        mm=6,
        yyyy=2024,
        abbreviated_project="TEST-PROJECT",
        additional_information="Additional test info",
        total_amount=10000000.0,
        tax=0.1,
        final_amount=9000000.0,
        expert_id=1,
        program_id=1,
        project_name="Test Project Full Name",
        summary_activities="Testing activities summary",
        activity_purpose="Purpose of activity",
        end_date=date(2099, 12, 31),
    )


@pytest.fixture
def mock_activity_single():
    """Create a single mock ActivityData instance."""
    return ActivityData(
        id=1,
        activity_number="01",
        activity_name="Test Activity 01",
        budget="10000000",
        working_days=5,
        rate=2000000.0,
        real_amount=10000000.0,
        contract_id=1,
    )


@pytest.fixture
def mock_activities_multiple():
    """Create multiple mock ActivityData instances."""
    return [
        ActivityData(
            id=1,
            activity_number="01",
            activity_name="Phan tich yeu cau",
            budget="5000000",
            working_days=3,
            rate=1500000.0,
            real_amount=4500000.0,
            contract_id=1,
        ),
        ActivityData(
            id=2,
            activity_number="02",
            activity_name="Thiet ke he thong",
            budget="8000000",
            working_days=5,
            rate=1600000.0,
            real_amount=8000000.0,
            contract_id=1,
        ),
        ActivityData(
            id=3,
            activity_number="03",
            activity_name="Phat trien ung dung",
            budget="12000000",
            working_days=10,
            rate=1200000.0,
            real_amount=12000000.0,
            contract_id=1,
        ),
    ]


@pytest.fixture
def mock_client():
    """Create a mock MezonClient."""
    client = MagicMock()
    client.channels = MagicMock()
    channel = AsyncMock()
    channel.send = AsyncMock()
    client.channels.fetch = AsyncMock(return_value=channel)

    upload_result = MagicMock()
    upload_result.url = "https://mezon.vn/files/test.docx"
    client.upload_file = AsyncMock(return_value=upload_result)

    return client


@pytest.fixture
def mock_s3_upload_service():
    """Create a mock S3UploadService."""
    service = MagicMock()
    service.upload_file = MagicMock(
        return_value="https://s3.example.com/files/test.docx"
    )
    return service


@pytest.fixture
def mock_contract_service():
    """Create a mock ContractService."""
    service = MagicMock()
    service.get_contract_by_id = AsyncMock()
    service.get_activities_by_contract_id = AsyncMock()
    service.finalize_contract = AsyncMock()
    service.create_contract = AsyncMock()
    service.update_contract = AsyncMock()
    service.delete_contract = AsyncMock()
    service.get_contracts_by_expert_id = AsyncMock()
    service.get_contracts_by_program_id = AsyncMock()
    service.get_contracts_by_year = AsyncMock()
    service.has_contract_order_in_project = AsyncMock()
    service.add_activity = AsyncMock()
    service.delete_activity = AsyncMock()
    service.resolve_program_code = AsyncMock()
    service.create_activity = AsyncMock()
    return service


@pytest.fixture
def mock_expert_service():
    """Create a mock ExpertService."""
    service = MagicMock()
    service.get_expert_by_id = AsyncMock()
    service.get_active_expert_by_id = AsyncMock()
    service.resolve_experts = AsyncMock()
    service.create_expert = AsyncMock()
    service.update_expert = AsyncMock()
    service.delete_expert = AsyncMock()
    service.list_all = AsyncMock()
    service.find_by_name = AsyncMock()
    service.find_by_id_number = AsyncMock()
    return service


@pytest.fixture
def mock_program_service():
    """Create a mock ProgramService."""
    service = MagicMock()
    service.get_program_by_code = AsyncMock()
    service.create_program = AsyncMock()
    service.update_program = AsyncMock()
    service.delete_program = AsyncMock()
    service.list_all = AsyncMock()
    return service


@pytest.fixture
def mock_word_export_service():
    """Create a mock WordExportService."""
    service = MagicMock()
    service.export_contract = MagicMock()
    service.export_acceptance_report = MagicMock()
    return service


@pytest.fixture
def exports_dir():
    """Create and clean up a temporary exports directory."""
    tmp_dir = tempfile.mkdtemp()
    yield tmp_dir
    # Cleanup
    for f in os.listdir(tmp_dir):
        os.unlink(os.path.join(tmp_dir, f))
    os.rmdir(tmp_dir)
