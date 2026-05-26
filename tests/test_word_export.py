"""Tests for WordExportService - contract and acceptance report exports."""

import os
import tempfile
import pytest
from datetime import date
from unittest.mock import patch, MagicMock

from app.services.contract.service import ContractData, ActivityData
from app.services.expert.service import ExpertData
from app.services.word_export import WordExportService


@pytest.fixture
def sample_expert():
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
def sample_contract():
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
        end_date=date(2024, 12, 31),
    )


@pytest.fixture
def sample_activities():
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
    ]


class TestWordExportServiceInit:
    """Test WordExportService initialization."""

    def test_default_template_paths(self):
        """Should initialize with default template paths."""
        service = WordExportService()
        assert service.template_path == "template/Template_HDCG.docx"
        assert service.acceptance_template_path == "template/Template_BBNT.docx"

    def test_custom_template_paths(self):
        """Should accept custom template paths."""
        service = WordExportService(
            template_path="/custom/path/contract.docx",
            acceptance_template_path="/custom/path/acceptance.docx",
        )
        assert service.template_path == "/custom/path/contract.docx"
        assert service.acceptance_template_path == "/custom/path/acceptance.docx"


class TestBuildAcceptanceContext:
    """Test _build_acceptance_context method."""

    def test_context_has_required_keys(self, sample_contract, sample_expert, sample_activities):
        """Should include all required context keys for template rendering."""
        service = WordExportService()
        context = service._build_acceptance_context(sample_contract, sample_expert, sample_activities)

        required_keys = [
            "order_id", "order", "dd", "mm", "yyyy",
            "pronoun", "expert_name", "nationality", "address",
            "id_number", "issued_date", "issued_place",
            "email_address", "phone", "bank_account", "bank_name",
            "sum_activities", "activity_purpose", "project_name", "end_date",
            "activities", "total_amount", "tax_amount", "final_amount", "text_amount",
        ]
        for key in required_keys:
            assert key in context, f"Missing key: {key}"

    def test_context_contract_values(self, sample_contract, sample_expert, sample_activities):
        """Should correctly map contract fields to context."""
        service = WordExportService()
        context = service._build_acceptance_context(
            sample_contract,
            sample_expert,
            sample_activities,
            acceptance_date=date(2024, 6, 1),
            acceptance_round="1",
            acceptance_additional_information="NT1",
        )

        assert context["order_id"] == "HDCG-2024-001/2024/HDCG-TEST-PROJECT-Additional test info"
        assert context["acceptance"] == "HDCG-2024-001/2024/BBNT-TEST-PROJECT-1"
        assert context["order"] == (
            "BIÊN BẢN BÀN GIAO VÀ NGHIỆM THU LẦN 1 "
            "HỢP ĐỒNG THUÊ KHOÁN CÔNG VIỆC"
        )
        assert context["dd"] == 1
        assert context["mm"] == 6
        assert context["yyyy"] == 2024
        assert context["abbreviated_project"] == "TEST-PROJECT"

    def test_context_expert_values(self, sample_contract, sample_expert, sample_activities):
        """Should correctly map expert fields to context."""
        service = WordExportService()
        context = service._build_acceptance_context(sample_contract, sample_expert, sample_activities)

        assert context["pronoun"] == "Ông"
        assert context["expert_name"] == "Nguyen Van A"
        assert context["nationality"] == "Viet Nam"
        assert context["id_number"] == "012345678901"
        assert context["issued_date"] == "15/01/2020"

    def test_context_activities_count(self, sample_contract, sample_expert, sample_activities):
        """Should include all activities in context."""
        service = WordExportService()
        context = service._build_acceptance_context(sample_contract, sample_expert, sample_activities)

        assert len(context["activities"]) == 2

    def test_context_activity_fields(self, sample_contract, sample_expert, sample_activities):
        """Each activity should have all required fields."""
        service = WordExportService()
        context = service._build_acceptance_context(sample_contract, sample_expert, sample_activities)

        act = context["activities"][0]
        assert "stt" in act
        assert "activity_number" in act
        assert "activity_name" in act
        assert "budget" in act
        assert "working_days" in act
        assert "rate" in act
        assert "real_amount" in act
        assert "real_amount_text" in act

    def test_context_activity_stt_starts_from_1(self, sample_contract, sample_expert, sample_activities):
        """Activity sequence numbers should start from 1."""
        service = WordExportService()
        context = service._build_acceptance_context(sample_contract, sample_expert, sample_activities)

        for idx, act in enumerate(context["activities"]):
            assert act["stt"] == idx + 1

    def test_context_amounts_are_strings(self, sample_contract, sample_expert, sample_activities):
        """Monetary amounts should be formatted as strings."""
        service = WordExportService()
        context = service._build_acceptance_context(sample_contract, sample_expert, sample_activities)

        assert isinstance(context["total_amount"], str)
        assert isinstance(context["tax_amount"], str)
        assert isinstance(context["final_amount"], str)
        assert isinstance(context["text_amount"], str)

    def test_context_totals_calculation_single_activity(self, sample_contract, sample_expert, sample_activities):
        """Should correctly calculate totals for single activity scenario."""
        service = WordExportService()
        single_activity = [sample_activities[0]]
        context = service._build_acceptance_context(sample_contract, sample_expert, single_activity)

        expected_total = 4500000.0
        expected_tax = expected_total * sample_contract.tax
        expected_final = expected_total - expected_tax

        assert context["total_amount"] == f"{expected_total:,.0f}".replace(",", ".")
        assert context["tax_amount"] == f"{expected_tax:,.0f}".replace(",", ".")
        assert context["final_amount"] == f"{expected_final:,.0f}".replace(",", ".")

    def test_context_totals_calculation_multiple_activities(self, sample_contract, sample_expert, sample_activities):
        """Should correctly calculate totals for multiple activities."""
        service = WordExportService()
        context = service._build_acceptance_context(sample_contract, sample_expert, sample_activities)

        expected_total = 4500000.0 + 8000000.0  # Sum of real_amounts
        expected_tax = expected_total * sample_contract.tax
        expected_final = expected_total - expected_tax

        assert context["total_amount"] == f"{expected_total:,.0f}".replace(",", ".")
        assert context["tax_amount"] == f"{expected_tax:,.0f}".replace(",", ".")
        assert context["final_amount"] == f"{expected_final:,.0f}".replace(",", ".")

    def test_context_null_fields_default_to_empty_string(self, sample_contract, sample_expert, sample_activities):
        """Optional None fields should default to empty string."""
        contract_no_optional = ContractData(
            id=1,
            order_id="HDCG-2024-001",
            dd=1,
            mm=6,
            yyyy=2024,
            abbreviated_project="",
            additional_information=None,
            total_amount=10000000.0,
            tax=0.1,
            final_amount=9000000.0,
            expert_id=1,
            program_id=1,
            project_name=None,
            summary_activities=None,
            activity_purpose=None,
            end_date=None,
        )
        service = WordExportService()
        context = service._build_acceptance_context(contract_no_optional, sample_expert, sample_activities)

        assert context["additional_information"] == ""
        assert context["project_name"] == ""
        assert context["sum_activities"] == ""
        assert context["activity_purpose"] == ""
        assert context["end_date"] == ""

    def test_context_additional_information_has_prefix(self, sample_contract, sample_expert, sample_activities):
        """additional_information should be prefixed with '- ' when not empty."""
        service = WordExportService()
        context = service._build_acceptance_context(sample_contract, sample_expert, sample_activities)
        assert context["additional_information"] == "- Additional test info"

    def test_context_activity_amounts_use_dot_separator(self, sample_contract, sample_expert, sample_activities):
        """Activity monetary amounts should use dot as thousand separator."""
        service = WordExportService()
        context = service._build_acceptance_context(sample_contract, sample_expert, sample_activities)
        assert context["activities"][0]["rate"] == "1.500.000"
        assert context["activities"][0]["real_amount"] == "4.500.000"

    def test_context_activity_supports_fractional_working_days(self, sample_contract, sample_expert, sample_activities):
        """Working days should preserve fractional values in export context."""
        sample_activities[0].working_days = 4.5
        service = WordExportService()
        context = service._build_acceptance_context(sample_contract, sample_expert, sample_activities)
        assert context["activities"][0]["working_days"] == "4.5"

    def test_context_expert_null_fields_default_to_empty_string(self, sample_contract, sample_expert, sample_activities):
        """Expert optional None fields should default to empty string."""
        expert_minimal = ExpertData(
            id=1,
            pronoun="Ông",
            expert_name="Test Expert",
        )
        service = WordExportService()
        context = service._build_acceptance_context(sample_contract, expert_minimal, sample_activities)

        assert context["nationality"] == ""
        assert context["address"] == ""
        assert context["id_number"] == ""
        assert context["issued_date"] == ""
        assert context["bank_account"] == ""
        assert context["bank_name"] == ""

    def test_context_end_date_format(self, sample_contract, sample_expert, sample_activities):
        """End date should be formatted as DD/MM/YYYY."""
        service = WordExportService()
        context = service._build_acceptance_context(sample_contract, sample_expert, sample_activities)

        assert context["end_date"] == "31/12/2024"


class TestExportAcceptanceReport:
    """Test export_acceptance_report method."""

    def test_export_creates_file(self, sample_contract, sample_expert, sample_activities):
        """Should create a Word file at the specified output path."""
        service = WordExportService()
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp:
            output_path = tmp.name

        try:
            result = service.export_acceptance_report(
                sample_contract, sample_expert, sample_activities, output_path
            )
            assert result == output_path
            assert os.path.exists(output_path)
            assert os.path.getsize(output_path) > 0
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_export_with_empty_activities(self, sample_contract, sample_expert):
        """Should handle empty activities list."""
        service = WordExportService()
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp:
            output_path = tmp.name

        try:
            result = service.export_acceptance_report(
                sample_contract, sample_expert, [], output_path
            )
            assert result == output_path
            assert os.path.exists(output_path)
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_export_with_single_activity(self, sample_contract, sample_expert, sample_activities):
        """Should correctly export with single activity."""
        service = WordExportService()
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp:
            output_path = tmp.name

        try:
            result = service.export_acceptance_report(
                sample_contract, sample_expert, [sample_activities[0]], output_path
            )
            assert result == output_path
            assert os.path.exists(output_path)
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    @patch("app.services.word_export.DocxTemplate")
    def test_export_calls_docxtpl_correctly(self, mock_docxtpl, sample_contract, sample_expert, sample_activities):
        """Should call DocxTemplate with correct template path and render context."""
        mock_doc = MagicMock()
        mock_docxtpl.return_value = mock_doc

        service = WordExportService()
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp:
            output_path = tmp.name

        try:
            service.export_acceptance_report(
                sample_contract, sample_expert, sample_activities, output_path
            )

            mock_docxtpl.assert_called_once_with("template/Template_BBNT.docx")
            mock_doc.render.assert_called_once()
            mock_doc.save.assert_called_once_with(output_path)
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    @patch("app.services.word_export.DocxTemplate")
    def test_export_context_has_correct_activity_count(self, mock_docxtpl, sample_contract, sample_expert, sample_activities):
        """Should pass correct number of activities to template context."""
        mock_doc = MagicMock()
        mock_docxtpl.return_value = mock_doc

        service = WordExportService()
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp:
            output_path = tmp.name

        try:
            service.export_acceptance_report(
                sample_contract, sample_expert, sample_activities, output_path
            )

            # Get the context passed to render
            call_args = mock_doc.render.call_args
            context = call_args[0][0]
            assert len(context["activities"]) == 2
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)


class TestBuildContextComparison:
    """Compare _build_context vs _build_acceptance_context for consistency."""

    def test_both_contexts_have_same_structure(self, sample_contract, sample_expert, sample_activities):
        """Both context builders should produce consistent key structures."""
        service = WordExportService()

        contract_context = service._build_context(sample_contract, sample_expert, sample_activities)
        acceptance_context = service._build_acceptance_context(sample_contract, sample_expert, sample_activities)

        # Both should have activities key
        assert "activities" in contract_context
        assert "activities" in acceptance_context

        # Both should have same number of activities
        assert len(contract_context["activities"]) == len(acceptance_context["activities"])

        # Both should have same basic keys
        basic_keys = [
            "order_id", "dd", "mm", "yyyy",
            "pronoun", "expert_name",
            "total_amount", "tax_amount", "final_amount", "text_amount",
        ]
        for key in basic_keys:
            assert key in contract_context
            assert key in acceptance_context

    def test_acceptance_context_has_different_totals(self, sample_contract, sample_expert, sample_activities):
        """Acceptance context should calculate totals differently (sum of selected activities)."""
        service = WordExportService()

        contract_context = service._build_context(sample_contract, sample_expert, sample_activities)
        acceptance_context = service._build_acceptance_context(sample_contract, sample_expert, sample_activities)

        # Contract total is from contract.total_amount
        assert contract_context["total_amount"] == "10.000.000"

        # Acceptance total is sum of activity real_amounts
        expected_acceptance_total = sum(act.real_amount for act in sample_activities)
        assert acceptance_context["total_amount"] == f"{expected_acceptance_total:,.0f}".replace(",", ".")

    def test_build_context_additional_information_has_prefix(self, sample_contract, sample_expert, sample_activities):
        """additional_information in _build_context should also be prefixed."""
        service = WordExportService()
        context = service._build_context(sample_contract, sample_expert, sample_activities)
        assert context["additional_information"] == "- Additional test info"
