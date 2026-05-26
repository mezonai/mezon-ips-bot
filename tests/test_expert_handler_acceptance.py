"""Tests for ExpertHandler acceptance report functionality."""

import os
import pytest
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.contract.service import ContractData, ActivityData
from app.services.expert.service import ExpertData
from app.services.bot.handlers.expert import ExpertHandler


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

    async def test_edit_contract_button_routed(
        self, handler, button_event
    ):
        """Should route edit_contract: button to _handle_edit_contract_button."""
        button_event.button_id = "edit_contract:1"
        handler._handle_edit_contract_button = AsyncMock()

        await handler.handle_button_click(button_event)

        handler._handle_edit_contract_button.assert_called_once_with(button_event, 1)


class TestExpertLookupByCccdOrName:
    """Test edit/delete lookup flow by CCCD or expert name."""

    async def test_handle_edit_resolves_by_cccd(
        self, handler, mock_expert_service, mock_expert
    ):
        """Should resolve edit target by CCCD."""
        handler.reply_message = AsyncMock()
        mock_expert_service.resolve_experts = AsyncMock(return_value=[mock_expert])

        await handler._handle_edit(MagicMock(), "012345678901")

        mock_expert_service.resolve_experts.assert_awaited_once_with("012345678901")
        handler.reply_message.assert_called_once()
        assert "Đang sửa thông tin chuyên gia" in handler.reply_message.call_args[0][1]

    async def test_handle_edit_resolves_by_name(
        self, handler, mock_expert_service, mock_expert
    ):
        """Should resolve edit target by expert name."""
        handler.reply_message = AsyncMock()
        mock_expert_service.resolve_experts = AsyncMock(return_value=[mock_expert])

        await handler._handle_edit(MagicMock(), "Nguyen Van A")

        mock_expert_service.resolve_experts.assert_awaited_once_with("Nguyen Van A")
        handler.reply_message.assert_called_once()
        assert "Đang sửa thông tin chuyên gia" in handler.reply_message.call_args[0][1]

    async def test_handle_edit_shows_ambiguous_matches(
        self, handler, mock_expert_service, mock_expert
    ):
        """Should ask user to disambiguate when name matches many experts."""
        handler.reply_message = AsyncMock()
        other = ExpertData(
            id=2,
            pronoun="Bà",
            expert_name="Nguyen Van A",
            id_number="999999999999",
        )
        mock_expert_service.resolve_experts = AsyncMock(return_value=[mock_expert, other])

        await handler._handle_edit(MagicMock(), "Nguyen Van A")

        handler.reply_message.assert_called_once()
        message_text = handler.reply_message.call_args[0][1]
        assert "Tìm thấy 2 chuyên gia trùng khớp" in message_text
        assert "Nguyen Van A | CCCD: 012345678901" in message_text
        components = handler.reply_message.call_args[1]["components"]
        component_ids = [mc.component_id for row in components for mc in row.components]
        assert "resolve_edit:1" in component_ids

    async def test_handle_edit_shows_cap_notice_for_many_matches(
        self, handler, mock_expert_service
    ):
        """Should tell user when only first 10 matches are shown."""
        handler.reply_message = AsyncMock()
        matches = [
            ExpertData(
                id=i,
                pronoun="Ông",
                expert_name=f"Nguyen Van {i}",
                id_number=f"{i:012d}",
            )
            for i in range(1, 12)
        ]
        mock_expert_service.resolve_experts = AsyncMock(return_value=matches)

        await handler._handle_edit(MagicMock(), "Nguyen")

        handler.reply_message.assert_called_once()
        assert "Hiển thị 10 kết quả đầu" in handler.reply_message.call_args[0][1]

    async def test_handle_delete_resolves_by_cccd(
        self, handler, mock_expert_service, mock_expert
    ):
        """Should resolve delete target by CCCD."""
        handler.reply_message = AsyncMock()
        mock_expert_service.resolve_experts = AsyncMock(return_value=[mock_expert])

        await handler._handle_delete(MagicMock(), "012345678901")

        mock_expert_service.resolve_experts.assert_awaited_once_with("012345678901")
        handler.reply_message.assert_called_once()
        assert "Xác nhận xóa chuyên gia" in handler.reply_message.call_args[0][1]

    async def test_handle_delete_not_found(self, handler, mock_expert_service):
        """Should report not found for unmatched keyword."""
        handler.reply_message = AsyncMock()
        mock_expert_service.resolve_experts = AsyncMock(return_value=[])

        await handler._handle_delete(MagicMock(), "khong ton tai")

        handler.reply_message.assert_called_once()
        assert "Không tìm thấy chuyên gia" in handler.reply_message.call_args[0][1]

    async def test_resolve_delete_button_routed(
        self, handler, button_event, mock_expert_service, mock_expert
    ):
        """Should continue delete flow after ambiguity selection."""
        button_event.button_id = "resolve_delete:1"
        mock_expert_service.get_active_expert_by_id = AsyncMock(return_value=mock_expert)

        await handler.handle_button_click(button_event)

        handler.edit_message.assert_called_once()
        assert "Xác nhận xóa chuyên gia" in handler.edit_message.call_args[0][2]

    async def test_resolve_edit_button_routed(
        self, handler, button_event, mock_expert_service, mock_expert
    ):
        """Should continue edit flow after ambiguity selection."""
        button_event.button_id = "resolve_edit:1"
        mock_expert_service.get_active_expert_by_id = AsyncMock(return_value=mock_expert)

        await handler.handle_button_click(button_event)

        handler.edit_message.assert_called_once()
        assert "Đang sửa thông tin chuyên gia" in handler.edit_message.call_args[0][2]


class TestSaveActivity:
    """Test fractional working days handling."""

    async def test_accepts_fractional_working_days(
        self, handler, button_event, mock_contract_service, mock_contract
    ):
        mock_contract_service.get_contract_by_id = AsyncMock(return_value=mock_contract)
        mock_contract_service.get_activities_by_contract_id = AsyncMock(return_value=[])
        mock_contract_service.add_activity = AsyncMock()

        await handler._handle_save_activity(
            button_event,
            1,
            {
                "activity_name": "Review",
                "budget": "1000000",
                "working_days": "4.5",
                "rate": "2000000",
            },
        )

        saved_activity = mock_contract_service.add_activity.await_args.args[1]
        assert saved_activity.working_days == 4.5
        assert saved_activity.real_amount == 9000000.0
        assert "Số ngày: 4.5" in handler.edit_message.call_args[0][2]

    async def test_ignores_duplicate_activity_submit_from_same_message(
        self, handler, button_event, mock_contract_service, mock_contract
    ):
        mock_contract_service.get_contract_by_id = AsyncMock(return_value=mock_contract)
        mock_contract_service.get_activities_by_contract_id = AsyncMock(return_value=[])
        mock_contract_service.add_activity = AsyncMock()
        payload = {
            "activity_name": "Review",
            "budget": "1000000",
            "working_days": "4.5",
            "rate": "2000000",
        }

        await handler._handle_save_activity(button_event, 1, payload)
        await handler._handle_save_activity(button_event, 1, payload)

        mock_contract_service.add_activity.assert_awaited_once()
        assert "đã được lưu trước đó" in handler.edit_message.call_args[0][2]


class TestEditContract:
    """Test contract edit flow."""

    async def test_shows_prefilled_edit_contract_form(
        self,
        handler,
        button_event,
        mock_contract_service,
        mock_contract,
        mock_expert_service,
        mock_expert,
    ):
        mock_contract_service.get_contract_by_id = AsyncMock(return_value=mock_contract)
        mock_expert_service.get_active_expert_by_id = AsyncMock(return_value=mock_expert)

        await handler._handle_edit_contract_button(button_event, 1)

        handler.edit_message.assert_called_once()
        assert "Đang sửa hợp đồng" in handler.edit_message.call_args[0][2]
        embeds = handler.edit_message.call_args[1]["embeds"]
        assert len(embeds) > 0
        components = handler.edit_message.call_args[1]["components"]
        component_ids = [mc.component_id for row in components for mc in row.components]
        assert "save_edit_contract:1" in component_ids

    async def test_updates_contract_from_edit_form(
        self,
        handler,
        button_event,
        mock_contract_service,
        mock_contract,
    ):
        updated_contract = ContractData(
            id=1,
            order_id="HD-NEW-001",
            dd=2,
            mm=6,
            yyyy=2024,
            abbreviated_project="TEST-PROJECT-2",
            additional_information="Updated info",
            total_amount=mock_contract.total_amount,
            tax=mock_contract.tax,
            final_amount=mock_contract.final_amount,
            expert_id=mock_contract.expert_id,
            program_id=2,
        )
        mock_contract_service.get_contract_by_id = AsyncMock(return_value=mock_contract)
        mock_contract_service.resolve_program_code = AsyncMock(return_value=2)
        mock_contract_service.has_contract_order_in_project = AsyncMock(return_value=False)
        mock_contract_service.update_contract = AsyncMock(return_value=updated_contract)

        await handler._handle_save_edit_contract(
            button_event,
            1,
            {
                "order_id": "HD-NEW-001",
                "contract_date": "02/06/2024",
                "program_code": "TEST-PROJECT-2",
                "additional_information": "Updated info",
            },
        )

        mock_contract_service.update_contract.assert_awaited_once()
        saved_data = mock_contract_service.update_contract.await_args.args[1]
        assert saved_data.order_id == "HD-NEW-001"
        assert saved_data.dd == 2
        assert saved_data.mm == 6
        assert saved_data.yyyy == 2024
        assert saved_data.abbreviated_project == "TEST-PROJECT-2"
        assert "Đã cập nhật hợp đồng" in handler.edit_message.call_args[0][2]
        assert "HD-NEW-001/2024/HDCG-TEST-PROJECT-2" in handler.edit_message.call_args[0][2]
