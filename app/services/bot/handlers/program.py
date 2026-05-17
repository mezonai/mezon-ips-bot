"""Program management handler with interactive forms."""

from __future__ import annotations

from datetime import date as date_type
from typing import Any

from mezon import ButtonBuilder, InteractiveBuilder
from mezon.models import (
    ButtonMessageStyle,
    InteractiveMessageProps,
    InputFieldOption,
    MessageActionRow,
    MessageComponent,
)
from mezon.protobuf.rtapi import realtime_pb2

from .base import BaseMessageHandler, command
from app.services.bot.form_tracker import form_tracker
from app.services.contract.service import ContractService
from app.services.program.service import ProgramData, ProgramService, normalize_program_code
from app.utils.formatters import format_currency_vn, format_date_vn


class ProgramHandler(BaseMessageHandler):
    """Handler for *program command to manage programs."""
    PAGE_SIZE = 10

    def __init__(
        self,
        client,
        program_service: ProgramService,
        contract_service: ContractService | None = None,
    ):
        super().__init__(client)
        self.program_service = program_service
        self.contract_service = contract_service

    def _build_buttons(
        self, buttons: list[tuple[str, str, ButtonMessageStyle]]
    ) -> list[MessageActionRow]:
        """Build MessageActionRow from button definitions."""
        bb = ButtonBuilder()
        for btn_id, label, style in buttons:
            bb.add_button(btn_id, label, style)
        return [
            MessageActionRow(components=[MessageComponent(**b) for b in bb.build()])
        ]

    @staticmethod
    def _paginate_items(
        items: list[Any], page: int, page_size: int
    ) -> tuple[list[Any], int, int]:
        """Return the requested slice with clamped page metadata."""
        total_items = len(items)
        total_pages = max(1, (total_items + page_size - 1) // page_size)
        current_page = min(max(page, 1), total_pages)
        start = (current_page - 1) * page_size
        end = start + page_size
        return items[start:end], current_page, total_pages

    def _build_pagination_components(
        self, prev_button_id: str | None, next_button_id: str | None
    ) -> list[MessageActionRow]:
        """Build previous/next pagination buttons when needed."""
        buttons: list[tuple[str, str, ButtonMessageStyle]] = []
        if prev_button_id:
            buttons.append(
                (prev_button_id, "⬅️ Trang trước", ButtonMessageStyle.SECONDARY)
            )
        if next_button_id:
            buttons.append(
                (next_button_id, "➡️ Trang sau", ButtonMessageStyle.SECONDARY)
            )
        return self._build_buttons(buttons) if buttons else []

    def _build_form_buttons(
        self, save_btn_id: str = "save", cancel_btn_id: str = "cancel"
    ) -> list[MessageActionRow]:
        return self._build_buttons(
            [
                (save_btn_id, "✅ Lưu", ButtonMessageStyle.SUCCESS),
                (cancel_btn_id, "❌ Hủy", ButtonMessageStyle.DANGER),
            ]
        )

    def _build_program_form(self, existing: ProgramData | None = None) -> InteractiveBuilder:
        """Build the interactive form for creating/editing a program."""
        title = "✏️ Sửa chương trình" if existing else "➕ Tạo chương trình mới"
        form = InteractiveBuilder(title)
        form.set_description("Quản lý thông tin chương trình/dự án")
        form.set_color("#5865F2")

        form.add_input_field(
            "program_code", "Mã chương trình",
            placeholder="PROJ-001",
            description="Mã định danh duy nhất",
            options=InputFieldOption(defaultValue=existing.program_code if existing else None),
        )
        form.add_input_field(
            "name", "Tên chương trình",
            placeholder="Dự án ABC",
            description="Tên đầy đủ của chương trình",
            options=InputFieldOption(defaultValue=existing.name if existing else None),
        )
        form.add_input_field(
            "start_date", "Ngày bắt đầu",
            placeholder="dd/mm/yyyy",
            description="Ngày bắt đầu dự án (dd/mm/yyyy)",
            options=InputFieldOption(defaultValue=format_date_vn(existing.start_date) if existing and existing.start_date else None),
        )
        form.add_input_field(
            "end_date", "Ngày kết thúc",
            placeholder="dd/mm/yyyy",
            description="Ngày hết hạn (dd/mm/yyyy)",
            options=InputFieldOption(defaultValue=format_date_vn(existing.end_date) if existing and existing.end_date else None),
        )
        form.add_input_field(
            "activity_purpose", "Mục đích hoạt động",
            placeholder="Tư vấn, phản biện...",
            description="Mục đích của các hoạt động",
            options=InputFieldOption(defaultValue=existing.activity_purpose if existing else None),
        )
        form.add_input_field(
            "summary_activities", "Tổng hợp hoạt động",
            placeholder="Mô tả ngắn...",
            description="Tóm tắt các hoạt động",
            options=InputFieldOption(textarea=True, defaultValue=existing.summary_activities if existing else None),
        )
        return form

    def _format_program(self, p: ProgramData) -> str:
        """Format a single program record."""
        lines = [
            f"📋 **{p.program_code}** — {p.name}",
            f"   🚀 Bắt đầu: {format_date_vn(p.start_date) if p.start_date else '—'}",
            f"   📅 Kết thúc: {format_date_vn(p.end_date) if p.end_date else '—'}",
            f"   🎯 Mục đích: {p.activity_purpose or '—'}",
            f"   📝 Tóm tắt: {p.summary_activities or '—'}",
        ]
        return "\n".join(lines)

    @staticmethod
    def _parse_optional_date(raw_value: str, field_label: str) -> date_type | None:
        """Parse dd/mm/yyyy into a date object."""
        value = raw_value.strip()
        if not value:
            return None
        try:
            d, m, y = value.split("/")
            return date_type(int(y), int(m), int(d))
        except (ValueError, IndexError) as exc:
            raise ValueError(f"{field_label} không hợp lệ. Format: dd/mm/yyyy") from exc

    def _build_program_action_buttons(self, program_id: int) -> list[MessageActionRow]:
        return self._build_buttons(
            [
                (f"view_program_contracts:{program_id}", "📋 DS hợp đồng", ButtonMessageStyle.SECONDARY),
                (f"edit_program:{program_id}", "✏️ Sửa", ButtonMessageStyle.PRIMARY),
                (f"delete_program:{program_id}", "🗑️ Xóa", ButtonMessageStyle.DANGER),
            ]
        )

    async def _show_program_detail(self, message, program: ProgramData) -> None:
        await self.reply_message(
            message,
            self._format_program(program),
            components=self._build_program_action_buttons(program.id),
        )

    @command("*program")
    async def handle_program(self, message, subcmd: str = None, rest: str = None) -> None:
        """Handle *program command."""
        if not subcmd:
            await self._handle_help(message)
            return

        if subcmd == "list":
            await self._handle_list(message)
        elif subcmd == "add":
            await self._handle_add(message)
        elif subcmd == "find":
            await self._handle_find(message, rest or "")
        elif subcmd == "edit":
            await self._handle_edit(message, rest or "")
        elif subcmd == "delete":
            await self._handle_delete(message, rest or "")
        else:
            code = normalize_program_code(
                " ".join(part for part in [subcmd, rest or ""] if part).strip()
            )
            if not code:
                await self._handle_help(message)
                return
            await self._handle_find(message, code)

    async def _handle_help(self, message) -> None:
        """Show help message."""
        help_text = """📋 **Quản lý chương trình**

**Lệnh:**
• `*program list` — Danh sách chương trình
• `*program add` — Thêm chương trình mới
• `*program <mã>` — Xem chương trình theo mã
• `*program find <mã>` — Tìm chương trình theo mã
• `*program edit <mã>` — Sửa chương trình
• `*program delete <mã>` — Xóa chương trình"""
        await self.reply_message(message, help_text)

    async def _render_program_list_message(self, message, page: int = 1) -> None:
        """Reply with a paginated program list."""
        programs = await self.program_service.list_programs()
        if not programs:
            await self.reply_message(message, "📋 Chưa có chương trình nào.")
            return

        page_items, current_page, total_pages = self._paginate_items(
            programs, page, self.PAGE_SIZE
        )
        lines = [
            f"📋 **Danh sách chương trình ({len(programs)}) - Trang {current_page}/{total_pages}:**\n"
        ]
        for p in page_items:
            lines.append(self._format_program(p))
            lines.append("")

        components = self._build_pagination_components(
            f"program_list_page:{current_page - 1}" if current_page > 1 else None,
            f"program_list_page:{current_page + 1}"
            if current_page < total_pages
            else None,
        )
        await self.reply_message(message, "\n".join(lines), components=components)

    async def _render_program_list_event(
        self, event: realtime_pb2.MessageButtonClicked, page: int
    ) -> None:
        """Edit message with a paginated program list."""
        programs = await self.program_service.list_programs()
        if not programs:
            await self.edit_message(
                event.channel_id,
                event.message_id,
                "📋 Chưa có chương trình nào.",
                components=[],
            )
            return

        page_items, current_page, total_pages = self._paginate_items(
            programs, page, self.PAGE_SIZE
        )
        lines = [
            f"📋 **Danh sách chương trình ({len(programs)}) - Trang {current_page}/{total_pages}:**\n"
        ]
        for p in page_items:
            lines.append(self._format_program(p))
            lines.append("")

        components = self._build_pagination_components(
            f"program_list_page:{current_page - 1}" if current_page > 1 else None,
            f"program_list_page:{current_page + 1}"
            if current_page < total_pages
            else None,
        )
        await self.edit_message(
            event.channel_id,
            event.message_id,
            "\n".join(lines),
            components=components,
        )

    async def _handle_list(self, message) -> None:
        """List all programs."""
        await self._render_program_list_message(message, page=1)

    async def _handle_add(self, message) -> None:
        """Show form to add a new program."""
        form = self._build_program_form()
        await self.reply_message(
            message,
            "➕ Tạo chương trình mới:",
            embeds=[InteractiveMessageProps(**form.build())],
            components=self._build_form_buttons("save_program", "cancel"),
        )

    async def _handle_find(self, message, code: str) -> None:
        """Find a program by code."""
        if not code:
            await self.reply_message(message, "❌ Thiếu mã chương trình. Dùng: `*program find <mã>`")
            return

        code = normalize_program_code(code)
        program = await self.program_service.get_program_by_code(code)
        if not program:
            await self.reply_message(message, f"❌ Không tìm thấy chương trình với mã `{code}`.")
            return

        await self._show_program_detail(message, program)

    async def _handle_edit(self, message, code: str) -> None:
        """Show form to edit a program."""
        if not code:
            await self.reply_message(message, "❌ Thiếu mã chương trình. Dùng: `*program edit <mã>`")
            return

        code = normalize_program_code(code)
        program = await self.program_service.get_program_by_code(code)
        if not program:
            await self.reply_message(message, f"❌ Không tìm thấy chương trình với mã `{code}`.")
            return

        form = self._build_program_form(program)
        await self.reply_message(
            message,
            f"✏️ Sửa chương trình: **{program.program_code}**",
            embeds=[InteractiveMessageProps(**form.build())],
            components=self._build_form_buttons(f"update_program:{program.id}", "cancel"),
        )

    async def _handle_delete(self, message, code: str) -> None:
        """Confirm deletion of a program."""
        if not code:
            await self.reply_message(message, "❌ Thiếu mã chương trình. Dùng: `*program delete <mã>`")
            return

        code = normalize_program_code(code)
        program = await self.program_service.get_program_by_code(code)
        if not program:
            await self.reply_message(message, f"❌ Không tìm thấy chương trình với mã `{code}`.")
            return

        await self.reply_message(
            message,
            f"⚠️ **Xác nhận xóa chương trình?**\n\n{self._format_program(program)}",
            components=self._build_buttons([
                (f"confirm_delete_program:{program.id}", "🗑️ Xác nhận xóa", ButtonMessageStyle.DANGER),
                ("cancel", "❌ Hủy", ButtonMessageStyle.SECONDARY),
            ]),
        )

    async def handle_button_click(self, event: realtime_pb2.MessageButtonClicked) -> None:
        """Handle button clicks."""
        button_id = event.button_id
        extra_data = form_tracker.parse_extra_data(event.extra_data)

        if button_id == "cancel":
            await self.edit_message(
                event.channel_id, event.message_id, "❌ Đã hủy.", components=[]
            )
        elif button_id == "save_program":
            await self._handle_save_program(event, extra_data)
        elif button_id.startswith("update_program:"):
            program_id = int(button_id.split(":")[1])
            await self._handle_update_program(event, program_id, extra_data)
        elif button_id.startswith("edit_program:"):
            program_id = int(button_id.split(":")[1])
            await self._handle_edit_program_button(event, program_id)
        elif button_id.startswith("delete_program:"):
            program_id = int(button_id.split(":")[1])
            await self._handle_delete_program_button(event, program_id)
        elif button_id.startswith("confirm_delete_program:"):
            program_id = int(button_id.split(":")[1])
            await self._handle_confirm_delete(event, program_id)
        elif button_id.startswith("view_program_contracts:"):
            program_id = int(button_id.split(":")[1])
            await self._handle_view_program_contracts(event, program_id)
        elif button_id.startswith("program_list_page:"):
            page = int(button_id.split(":")[1])
            await self._render_program_list_event(event, page)
        elif button_id.startswith("program_contracts_page:"):
            _, program_id_str, page_str = button_id.split(":")
            await self._handle_view_program_contracts(
                event, int(program_id_str), int(page_str)
            )

    async def _handle_view_program_contracts(
        self, event: realtime_pb2.MessageButtonClicked, program_id: int, page: int = 1
    ) -> None:
        """Show contracts under one program."""
        if not self.contract_service:
            await self.edit_message(
                event.channel_id, event.message_id, "❌ Contract service không khả dụng.", components=[]
            )
            return

        program = await self.program_service.get_program_by_id(program_id)
        if not program:
            await self.edit_message(
                event.channel_id, event.message_id, "❌ Không tìm thấy chương trình.", components=[]
            )
            return

        contracts = await self.contract_service.get_contracts_by_program_id(program_id)
        if not contracts:
            await self.edit_message(
                event.channel_id,
                event.message_id,
                f"📋 Chưa có hợp đồng nào trong chương trình **{program.program_code}**.",
                components=[],
            )
            return

        page_items, current_page, total_pages = self._paginate_items(
            contracts, page, self.PAGE_SIZE
        )
        lines = [
            f"📋 **Danh sách hợp đồng: {program.program_code} - {program.name} - Trang {current_page}/{total_pages}**\n"
        ]
        for contract in page_items:
            activities = await self.contract_service.get_activities_by_contract_id(contract.id)
            lines.append(
                f"• **{contract.order_id}** ({contract.dd:02d}/{contract.mm:02d}/{contract.yyyy})\n"
                f"  Hoạt động: {len(activities)} | Tổng: {format_currency_vn(contract.total_amount)} | Thực nhận: {format_currency_vn(contract.final_amount)}"
            )
            lines.append("")

        await self.edit_message(
            event.channel_id,
            event.message_id,
            "\n".join(lines),
            components=self._build_pagination_components(
                f"program_contracts_page:{program.id}:{current_page - 1}"
                if current_page > 1
                else None,
                f"program_contracts_page:{program.id}:{current_page + 1}"
                if current_page < total_pages
                else None,
            )
            + self._build_buttons(
                [(f"edit_program:{program.id}", "✏️ Sửa CT", ButtonMessageStyle.PRIMARY)]
            ),
        )

    async def _handle_save_program(
        self, event: realtime_pb2.MessageButtonClicked, extra_data: dict[str, Any]
    ) -> None:
        """Handle save new program."""
        try:
            program_code = normalize_program_code(extra_data.get("program_code", ""))
            name = extra_data.get("name", "").strip()

            if not program_code or not name:
                await self.edit_message(
                    event.channel_id, event.message_id,
                    "❌ Thiếu mã chương trình hoặc tên.", components=[]
                )
                return

            # Check duplicate
            existing = await self.program_service.get_program_by_code(program_code)
            if existing:
                await self.edit_message(
                    event.channel_id, event.message_id,
                    f"❌ Mã chương trình `{program_code}` đã tồn tại.", components=[]
                )
                return

            try:
                start_date = self._parse_optional_date(
                    extra_data.get("start_date", ""),
                    "Ngày bắt đầu",
                )
                end_date = self._parse_optional_date(
                    extra_data.get("end_date", ""),
                    "Ngày kết thúc",
                )
            except ValueError as exc:
                await self.edit_message(
                    event.channel_id, event.message_id, f"❌ {exc}", components=[]
                )
                return

            program_data = ProgramData(
                id=0,
                program_code=program_code,
                name=name,
                summary_activities=extra_data.get("summary_activities"),
                activity_purpose=extra_data.get("activity_purpose"),
                start_date=start_date,
                end_date=end_date,
            )

            created = await self.program_service.create_program(program_data)

            # Clear form data
            form_tracker.clear_form_data(str(event.message_id))

            await self.edit_message(
                event.channel_id, event.message_id,
                f"✅ Đã tạo chương trình **{created.program_code}**\n\n{self._format_program(created)}",
                components=[],
            )
        except ValueError as e:
            await self.edit_message(
                event.channel_id, event.message_id, f"❌ {e}", components=[]
            )
        except Exception as e:
            self.logger.error("Error saving program: %s", e, exc_info=True)
            await self.edit_message(
                event.channel_id, event.message_id, f"❌ Lỗi tạo chương trình: {e}", components=[]
            )

    async def _handle_update_program(
        self, event: realtime_pb2.MessageButtonClicked, program_id: int, extra_data: dict[str, Any]
    ) -> None:
        """Handle update existing program."""
        try:
            program_code = normalize_program_code(extra_data.get("program_code", ""))
            name = extra_data.get("name", "").strip()

            if not program_code or not name:
                await self.edit_message(
                    event.channel_id, event.message_id,
                    "❌ Thiếu mã chương trình hoặc tên.", components=[]
                )
                return

            try:
                start_date = self._parse_optional_date(
                    extra_data.get("start_date", ""),
                    "Ngày bắt đầu",
                )
                end_date = self._parse_optional_date(
                    extra_data.get("end_date", ""),
                    "Ngày kết thúc",
                )
            except ValueError as exc:
                await self.edit_message(
                    event.channel_id, event.message_id, f"❌ {exc}", components=[]
                )
                return

            program_data = ProgramData(
                id=program_id,
                program_code=program_code,
                name=name,
                summary_activities=extra_data.get("summary_activities"),
                activity_purpose=extra_data.get("activity_purpose"),
                start_date=start_date,
                end_date=end_date,
            )

            updated = await self.program_service.update_program(program_id, program_data)
            if not updated:
                await self.edit_message(
                    event.channel_id, event.message_id,
                    "❌ Không tìm thấy chương trình.", components=[]
                )
                return

            # Clear form data
            form_tracker.clear_form_data(str(event.message_id))

            await self.edit_message(
                event.channel_id, event.message_id,
                f"✅ Đã cập nhật chương trình **{updated.program_code}**\n\n{self._format_program(updated)}",
                components=[],
            )
        except ValueError as e:
            await self.edit_message(
                event.channel_id, event.message_id, f"❌ {e}", components=[]
            )
        except Exception as e:
            self.logger.error("Error updating program: %s", e, exc_info=True)
            await self.edit_message(
                event.channel_id, event.message_id, f"❌ Lỗi cập nhật chương trình: {e}", components=[]
            )

    async def _handle_edit_program_button(
        self, event: realtime_pb2.MessageButtonClicked, program_id: int
    ) -> None:
        """Handle edit button click."""
        program = await self.program_service.get_program_by_id(program_id)
        if not program:
            await self.edit_message(
                event.channel_id, event.message_id,
                "❌ Không tìm thấy chương trình.", components=[]
            )
            return

        form = self._build_program_form(program)
        await self.edit_message(
            event.channel_id, event.message_id,
            f"✏️ Sửa chương trình: **{program.program_code}**",
            embeds=[InteractiveMessageProps(**form.build())],
            components=self._build_form_buttons(f"update_program:{program.id}", "cancel"),
        )

    async def _handle_delete_program_button(
        self, event: realtime_pb2.MessageButtonClicked, program_id: int
    ) -> None:
        """Handle delete button click."""
        program = await self.program_service.get_program_by_id(program_id)
        if not program:
            await self.edit_message(
                event.channel_id, event.message_id,
                "❌ Không tìm thấy chương trình.", components=[]
            )
            return

        await self.edit_message(
            event.channel_id, event.message_id,
            f"⚠️ **Xác nhận xóa chương trình?**\n\n{self._format_program(program)}",
            components=self._build_buttons([
                (f"confirm_delete_program:{program.id}", "🗑️ Xác nhận xóa", ButtonMessageStyle.DANGER),
                ("cancel", "❌ Hủy", ButtonMessageStyle.SECONDARY),
            ]),
        )

    async def _handle_confirm_delete(
        self, event: realtime_pb2.MessageButtonClicked, program_id: int
    ) -> None:
        """Handle confirmed deletion."""
        program = await self.program_service.get_program_by_id(program_id)
        if not program:
            await self.edit_message(
                event.channel_id, event.message_id,
                "❌ Không tìm thấy chương trình.", components=[]
            )
            return

        success = await self.program_service.delete_program(program_id)
        if success:
            await self.edit_message(
                event.channel_id, event.message_id,
                f"✅ Đã xóa chương trình **{program.program_code}**", components=[]
            )
        else:
            await self.edit_message(
                event.channel_id, event.message_id,
                "❌ Không thể xóa chương trình.", components=[]
            )
