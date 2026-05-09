"""Tests for ExpertHandler acceptance report functionality."""

import os
import pytest
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.contract.service import ContractData, ActivityData
from app.services.expert.service import ExpertData
from app.services.bot.handlers.expert import ExpertHandler


@pytest.fixture
def mock_word_export_service():
    """Create a mock WordExportService."""
    service = MagicMock()
    service.export_contract = MagicMock()
    service.export_acceptance_report = MagicMock()
    return service


@pytest.fixture
def handler(mock_client, mock_contract_service, mock_expert_service, mock_program_service, mock_word_export_service):
    """Create an ExpertHandler with mocked dependencies."""
    h = ExpertHandler(
        client=mock_client,
        expert_service=mock_expert_service,
        contract_service=mock_contract_service,
        program_service=mock_program_service,
        word_export_service=mock_word_export_service,
        s3_upload_service=None,
    )
    h.edit_message = AsyncMock()
    return h


@pytest.fixture
def handler_with_s3(mock_client, mock_contract_service, mock_expert_service, mock_program_service, mock_word_export_service, mock_s3_upload_service):
    """Create an ExpertHandler with S3 upload service."""
    h = ExpertHandler(
        client=mock_client,
        expert_service=mock_expert_service,
        contract_service=mock_contract_service,
        program_service=mock_program_service,
        word_export_service=mock_word_export_service,
        s3_upload_service=mock_s3_upload_service,
    )
    h.edit_message = AsyncMock()
    return h


@pytest.fixture
def button_event():
    """Create a mock MessageButtonClicked event."""
    event = MagicMock()
    event.channel_id = 12345
    event.message_id = 67890
    event.user_id = 111
    event.button_id = "test_button"
    event.extra_data = ""
    return event


class TestHandleAcceptanceReport:
    """Test _handle_acceptance_report method."""

    async def test_handles_no_contract_service(self, handler, button_event):
        """Should show error when contract service is not available."""
        handler.contract_service = None
        await handler._handle_acceptance_report(button_event, 1)

        handler.edit_message.assert_called_once()
        assert "Contract service không khả dụng" in handler.edit_message.call_args[0][2]

    async def test_handles_contract_not_found(self, handler, button_event, mock_contract_service):
        """Should show error when contract is not found."""
        mock_contract_service.get_contract_by_id = AsyncMock(return_value=None)

        await handler._handle_acceptance_report(button_event, 1)

        handler.edit_message.assert_called_once()
        assert "Không tìm thấy hợp đồng" in handler.edit_message.call_args[0][2]

    async def test_handles_no_activities(
        self, handler, button_event, mock_contract_service, mock_contract
    ):
        """Should show error when contract has no activities."""
        mock_contract_service.get_contract_by_id = AsyncMock(return_value=mock_contract)
        mock_contract_service.get_activities_by_contract_id = AsyncMock(return_value=[])

        await handler._handle_acceptance_report(button_event, 1)

        handler.edit_message.assert_called_once()
        assert "Hợp đồng chưa có hoạt động nào" in handler.edit_message.call_args[0][2]

    async def test_single_activity_exports_directly(
        self, handler, button_event, mock_contract_service, mock_contract,
        mock_activity_single, mock_word_export_service
    ):
        """Should export directly when there's only 1 activity."""
        mock_contract_service.get_contract_by_id = AsyncMock(return_value=mock_contract)
        mock_contract_service.get_activities_by_contract_id = AsyncMock(return_value=[mock_activity_single])

        await handler._handle_acceptance_report(button_event, 1)

        assert handler.edit_message.called

    async def test_multiple_activities_shows_form(
        self, handler, button_event, mock_contract_service, mock_contract,
        mock_activities_multiple
    ):
        """Should show radio form when there are multiple activities."""
        mock_contract_service.get_contract_by_id = AsyncMock(return_value=mock_contract)
        mock_contract_service.get_activities_by_contract_id = AsyncMock(return_value=mock_activities_multiple)

        await handler._handle_acceptance_report(button_event, 1)

        handler.edit_message.assert_called_once()
        assert "Chọn hoạt động cần nghiệm thu" in handler.edit_message.call_args[0][2]
        embeds = handler.edit_message.call_args[1]["embeds"]
        assert len(embeds) > 0


class TestShowActivitySelectionForm:
    """Test _show_activity_selection_form method."""

    async def test_creates_radio_form(
        self, handler, button_event, mock_activities_multiple
    ):
        """Should create a form with radio buttons for each activity."""
        await handler._show_activity_selection_form(
            button_event, 1, mock_activities_multiple
        )

        handler.edit_message.assert_called_once()
        # Check embed has the form
        call_kwargs = handler.edit_message.call_args[1]
        embeds = call_kwargs["embeds"]
        assert len(embeds) > 0

    async def test_includes_export_and_cancel_buttons(
        self, handler, button_event, mock_activities_multiple
    ):
        """Should include export and cancel buttons."""
        await handler._show_activity_selection_form(
            button_event, 1, mock_activities_multiple
        )

        components = handler.edit_message.call_args[1]["components"]
        component_ids = []
        for row in components:
            for mc in row.components:
                component_ids.append(mc.component_id)

        assert "export_acceptance:1" in component_ids
        assert "cancel" in component_ids


class TestExportAcceptanceDirect:
    """Test _export_acceptance_direct method."""

    async def test_handles_no_word_export_service(
        self, handler, button_event, mock_contract
    ):
        """Should show error when word export service is not available."""
        handler.word_export_service = None
        handler.contract_service = MagicMock()
        handler.contract_service.get_contract_by_id = AsyncMock(return_value=mock_contract)

        await handler._export_acceptance_direct(button_event, 1, [])

        assert "Service không khả dụng" in handler.edit_message.call_args[0][2]

    async def test_exports_with_valid_data(
        self, handler, button_event, mock_contract_service, mock_contract,
        mock_expert_service, mock_expert, mock_activities_multiple,
        mock_word_export_service
    ):
        """Should export acceptance report with valid data."""
        mock_contract_service.get_contract_by_id = AsyncMock(return_value=mock_contract)
        mock_expert_service.get_expert_by_id = AsyncMock(return_value=mock_expert)
        mock_word_export_service.export_acceptance_report = MagicMock(
            return_value="/tmp/test_bbnt.docx"
        )

        test_file = "/tmp/test_bbnt.docx"
        with open(test_file, "w") as f:
            f.write("test content")

        try:
            await handler._export_acceptance_direct(
                button_event, 1, mock_activities_multiple
            )
            mock_word_export_service.export_acceptance_report.assert_called_once()
        finally:
            if os.path.exists(test_file):
                os.unlink(test_file)


class TestHandleExportAcceptance:
    """Test _handle_export_acceptance method."""

    async def test_handles_no_contract_service(self, handler, button_event):
        """Should show error when contract service is not available."""
        handler.contract_service = None
        await handler._handle_export_acceptance(button_event, 1, {})

        assert "Service không khả dụng" in handler.edit_message.call_args[0][2]

    async def test_handles_no_selection(self, handler, button_event):
        """Should show error when no activities are selected."""
        await handler._handle_export_acceptance(button_event, 1, {"selected_activity_ids": []})

        assert "Vui lòng chọn ít nhất 1 hoạt động" in handler.edit_message.call_args[0][2]

    async def test_handles_no_matching_activities(
        self, handler, button_event, mock_contract_service
    ):
        """Should show error when selected activities don't exist."""
        mock_contract_service.get_activities_by_contract_id = AsyncMock(return_value=[])

        await handler._handle_export_acceptance(button_event, 1, {"selected_activity_ids": ["999"]})

        assert "Không tìm thấy hoạt động đã chọn" in handler.edit_message.call_args[0][2]

    async def test_exports_selected_activities(
        self, handler, button_event, mock_contract_service, mock_activities_multiple
    ):
        """Should export only the selected activities."""
        mock_contract_service.get_activities_by_contract_id = AsyncMock(
            return_value=mock_activities_multiple
        )

        handler._export_acceptance_direct = AsyncMock()

        await handler._handle_export_acceptance(button_event, 1, {"selected_activity_ids": ["2"]})

        handler._export_acceptance_direct.assert_called_once()
        call_args = handler._export_acceptance_direct.call_args
        # Should only pass activity with id=2
        assert len(call_args[0][2]) == 1
        assert call_args[0][2][0].id == 2

    async def test_exports_multiple_selected_activities(
        self, handler, button_event, mock_contract_service, mock_activities_multiple
    ):
        """Should export multiple selected activities (comma-separated IDs)."""
        mock_contract_service.get_activities_by_contract_id = AsyncMock(
            return_value=mock_activities_multiple
        )

        handler._export_acceptance_direct = AsyncMock()

        await handler._handle_export_acceptance(button_event, 1, {"selected_activity_ids": ["1", "3"]})

        handler._export_acceptance_direct.assert_called_once()
        call_args = handler._export_acceptance_direct.call_args
        # Should pass activities with id=1 and id=3
        assert len(call_args[0][2]) == 2
        selected_ids = {act.id for act in call_args[0][2]}
        assert selected_ids == {1, 3}


class TestButtonRouting:
    """Test button click routing for acceptance report buttons."""

    async def test_acceptance_report_button_routed(
        self, handler, button_event, mock_contract_service
    ):
        """Should route acceptance_report: button to _handle_acceptance_report."""
        button_event.button_id = "acceptance_report:1"
        handler._handle_acceptance_report = AsyncMock()

        await handler.handle_button_click(button_event)

        handler._handle_acceptance_report.assert_called_once_with(button_event, 1)

    async def test_export_acceptance_button_routed(
        self, handler, button_event, mock_contract_service
    ):
        """Should route export_acceptance: button to _handle_export_acceptance."""
        button_event.button_id = "export_acceptance:1"
        handler._handle_export_acceptance = AsyncMock()

        await handler.handle_button_click(button_event)

        handler._handle_export_acceptance.assert_called_once()
