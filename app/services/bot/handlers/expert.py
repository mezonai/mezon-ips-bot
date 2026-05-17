"""Expert management handler with interactive forms."""

from __future__ import annotations

from datetime import date as date_type
from typing import Any

from mezon import ButtonBuilder, InteractiveBuilder
from mezon.models import (
    ApiMessageAttachment,
    ButtonMessageStyle,
    ChannelMessageContent,
    InteractiveMessageProps,
    InputFieldOption,
    MessageActionRow,
    MessageComponent,
    RadioFieldOption,
)
from mezon.protobuf.rtapi import realtime_pb2

from .base import BaseMessageHandler, command
from app.services.bot.form_tracker import form_tracker
from app.services.expert.service import ExpertService, ExpertData
from app.services.contract.service import ContractService, ContractData, ActivityData
from app.services.program.service import ProgramService, normalize_program_code
from app.services.word_export import WordExportService
from app.services.s3_upload import S3UploadService
from app.utils.formatters import format_currency_vn, format_date_vn
from app.utils import number_to_vietnamese_text


class ExpertHandler(BaseMessageHandler):
    """Handler for *expert command to manage experts."""

    def __init__(
        self,
        client,
        expert_service: ExpertService,
        contract_service: ContractService | None = None,
        program_service: ProgramService | None = None,
        word_export_service: WordExportService | None = None,
        s3_upload_service: S3UploadService | None = None,
    ):
        super().__init__(client)
        self.expert_service = expert_service
        self.contract_service = contract_service
        self.program_service = program_service
        self.word_export_service = word_export_service
        self.s3_upload_service = s3_upload_service
        self._processed_activity_submits: set[str] = set()

    def _build_buttons(
        self, buttons: list[tuple[str, str, ButtonMessageStyle]]
    ) -> list[MessageActionRow]:
        """Build MessageActionRow from button definitions."""
        bb = ButtonBuilder()
        for btn_id, label, style in buttons:
            if style == ButtonMessageStyle.LINK:
                pass  # skip for now
            bb.add_button(btn_id, label, style)
        return [
            MessageActionRow(components=[MessageComponent(**b) for b in bb.build()])
        ]

    @staticmethod
    def _format_working_days(working_days: float) -> str:
        """Format working days without trailing .0."""
        return f"{working_days:g}"

    def _build_form_buttons(
        self, save_btn_id: str = "save", cancel_btn_id: str = "cancel"
    ) -> list[MessageActionRow]:
        return self._build_buttons(
            [
                (save_btn_id, "✅ Lưu", ButtonMessageStyle.SUCCESS),
                (cancel_btn_id, "❌ Hủy", ButtonMessageStyle.DANGER),
            ]
        )

    def _build_edit_buttons(self, prof_id: int) -> list[MessageActionRow]:
        return self._build_buttons(
            [
                (f"save_edit:{prof_id}", "✅ Cập nhật", ButtonMessageStyle.SUCCESS),
                ("cancel", "❌ Hủy", ButtonMessageStyle.DANGER),
            ]
        )

    def _build_delete_buttons(self, prof_id: int) -> list[MessageActionRow]:
        return self._build_buttons(
            [
                (
                    f"delete_confirm:{prof_id}",
                    "🗑️ Xác nhận xóa",
                    ButtonMessageStyle.DANGER,
                ),
                ("cancel", "❌ Hủy", ButtonMessageStyle.SECONDARY),
            ]
        )

    def _build_find_buttons(self, prof_id: int) -> list[MessageActionRow]:
        return self._build_buttons(
            [
                (
                    f"create_contract:{prof_id}",
                    "📝 Tạo hợp đồng",
                    ButtonMessageStyle.PRIMARY,
                ),
                (
                    f"list_contracts:{prof_id}",
                    "📋 Danh sách HĐ",
                    ButtonMessageStyle.SECONDARY,
                ),
            ]
        )

    def _build_contract_action_buttons(self, prof_id: int) -> list[MessageActionRow]:
        return self._build_buttons(
            [
                (
                    f"save_contract:{prof_id}",
                    "✅ Tạo hợp đồng",
                    ButtonMessageStyle.SUCCESS,
                ),
                ("cancel", "❌ Hủy", ButtonMessageStyle.DANGER),
            ]
        )

    def _build_activity_buttons(self, contract_id: int) -> list[MessageActionRow]:
        return self._build_buttons(
            [
                (
                    f"save_activity:{contract_id}",
                    "✅ Lưu activity",
                    ButtonMessageStyle.SUCCESS,
                ),
                ("cancel", "❌ Hủy", ButtonMessageStyle.DANGER),
            ]
        )

    def _build_after_activity_buttons(self, contract_id: int) -> list[MessageActionRow]:
        return self._build_buttons(
            [
                (
                    f"add_more_activity:{contract_id}",
                    "➕ Thêm activity",
                    ButtonMessageStyle.PRIMARY,
                ),
                (
                    f"finalize_contract:{contract_id}",
                    "✅ Hoàn tất",
                    ButtonMessageStyle.SUCCESS,
                ),
                ("cancel", "❌ Hủy", ButtonMessageStyle.DANGER),
            ]
        )

    def _build_finalized_buttons(self, contract_id: int) -> list[MessageActionRow]:
        return self._build_buttons(
            [
                (
                    f"export_word:{contract_id}",
                    "📄 Xuất file Word",
                    ButtonMessageStyle.SUCCESS,
                ),
            ]
        )

    def _build_contract_list_buttons(self, contract_id: int) -> list[MessageActionRow]:
        return self._build_buttons(
            [
                (
                    f"view_contract:{contract_id}",
                    "📄 Xem chi tiết",
                    ButtonMessageStyle.PRIMARY,
                ),
                (f"edit_contract:{contract_id}", "✏️ Sửa", ButtonMessageStyle.SECONDARY),
                (
                    f"delete_contract_confirm:{contract_id}",
                    "🗑️ Xóa",
                    ButtonMessageStyle.DANGER,
                ),
                ("cancel", "⬅️ Quay lại", ButtonMessageStyle.SECONDARY),
            ]
        )

    def _build_contract_list_rows(
        self, prof_id: int, contracts: list, allow_create: bool = True
    ) -> list[MessageActionRow]:
        """Build button rows for contract list, one button per contract."""
        rows = []
        for c in contracts:
            bb = ButtonBuilder()
            bb.add_button(
                f"view_contract:{c.id}", f"📄 {c.order_id}", ButtonMessageStyle.PRIMARY
            )
            built = bb.build()
            rows.append(
                MessageActionRow(components=[MessageComponent(**b) for b in built])
            )

        bb2 = ButtonBuilder()
        if allow_create:
            bb2.add_button(
                f"create_contract:{prof_id}",
                "➕ Tạo hợp đồng mới",
                ButtonMessageStyle.SUCCESS,
            )
        bb2.add_button("cancel", "⬅️ Quay lại", ButtonMessageStyle.SECONDARY)
        built2 = bb2.build()
        rows.append(
            MessageActionRow(components=[MessageComponent(**b) for b in built2])
        )

        return rows

    def _build_add_form(self) -> InteractiveBuilder:
        """Build the interactive form for adding a new expert."""
        form = InteractiveBuilder("➕ Thêm chuyên gia mới")
        form.set_description("Điền thông tin chuyên gia bên dưới")
        form.set_color("#5865F2")

        form.add_radio_field(
            "pronoun",
            "Xưng hô",
            options=[
                RadioFieldOption(label="Ông", value="Ông"),
                RadioFieldOption(label="Bà", value="Bà"),
            ],
        )
        form.add_input_field(
            "expert_name",
            "Họ và tên",
            placeholder="Nguyễn Văn A",
        )
        form.add_input_field(
            "nationality",
            "Quốc tịch",
            placeholder="Việt Nam",
        )
        form.add_input_field(
            "address",
            "Địa chỉ",
            placeholder="Số nhà, đường, phường/xã, quận/huyện, tỉnh/thành phố",
            options=InputFieldOption(textarea=True),
        )
        form.add_input_field(
            "id_number",
            "Số CCCD",
            placeholder="012345678901",
        )
        form.add_input_field(
            "issued_date",
            "Ngày cấp CCCD",
        )
        form.add_input_field(
            "issued_place",
            "Nơi cấp",
            options=InputFieldOption(defaultValue="Cục CSQLHC về TTXH")
        )
        form.add_input_field(
            "email_address",
            "Email",
            placeholder="email@example.com",
            options=InputFieldOption(type="email"),
        )
        form.add_input_field(
            "phone",
            "Số điện thoại",
            placeholder="0912345678",
        )
        form.add_input_field(
            "bank_account",
            "Số tài khoản ngân hàng",
            placeholder="1234567890",
        )
        form.add_input_field(
            "bank_name",
            "Ngân hàng",
            placeholder="Ngân hàng TMCP Kỹ Thương Việt Nam",
        )
        return form

    def _build_edit_form(self, p: ExpertData) -> InteractiveBuilder:
        """Build the interactive form for editing an expert."""
        form = InteractiveBuilder(f"✏️ Sửa thông tin: {p.pronoun} {p.expert_name}")
        form.set_description("Chỉnh sửa thông tin chuyên gia")
        form.set_color("#F59E0B")

        form.add_radio_field(
            "pronoun",
            "Xưng hô",
            options=[
                RadioFieldOption(label="Ông", value="Ông"),
                RadioFieldOption(label="Bà", value="Bà"),
            ],
        )
        # Mark current pronoun as selected
        current = (p.pronoun or "").strip()
        for i, opt in enumerate(form.interactive["fields"][-1]["inputs"]["component"]):
            if opt["value"] == current:
                form.interactive["fields"][-1]["inputs"]["component"][i]["selected"] = True

        form.add_input_field(
            "expert_name",
            "Họ và tên",
            placeholder="Nguyễn Văn A",
            options=InputFieldOption(defaultValue=p.expert_name),
        )
        form.add_input_field(
            "nationality",
            "Quốc tịch",
            placeholder="Việt Nam",
            options=InputFieldOption(defaultValue=p.nationality or ""),
        )
        form.add_input_field(
            "address",
            "Địa chỉ",
            placeholder="Địa chỉ liên hệ",
            options=InputFieldOption(textarea=True, defaultValue=p.address or ""),
        )
        form.add_input_field(
            "id_number",
            "Số CCCD",
            placeholder="012345678901",
            options=InputFieldOption(defaultValue=p.id_number or ""),
        )
        form.add_input_field(
            "issued_date",
            "Ngày cấp",
            placeholder="dd/mm/yyyy",
            options=InputFieldOption(
                defaultValue=format_date_vn(p.issued_date) if p.issued_date else ""
            )
        )
        form.add_input_field(
            "issued_place",
            "Nơi cấp",
            placeholder="Nơi cấp CCCD",
            options=InputFieldOption(defaultValue=p.issued_place or ""),
        )
        form.add_input_field(
            "email_address",
            "Email",
            placeholder="email@example.com",
            options=InputFieldOption(type="email", defaultValue=p.email_address or ""),
        )
        form.add_input_field(
            "phone",
            "Số điện thoại",
            placeholder="0912345678",
            options=InputFieldOption(defaultValue=p.phone or ""),
        )
        form.add_input_field(
            "bank_account",
            "Số tài khoản",
            placeholder="1234567890",
            options=InputFieldOption(defaultValue=p.bank_account or ""),
        )
        form.add_input_field(
            "bank_name",
            "Ngân hàng",
            placeholder="Ngân hàng TMCP Kỹ Thương Việt Nam",
            options=InputFieldOption(defaultValue=p.bank_name or ""),
        )
        return form

    def _build_contract_form(self, prof: ExpertData) -> InteractiveBuilder:
        """Build the interactive form for creating a new contract."""
        form = InteractiveBuilder("📝 Tạo hợp đồng chuyên gia")
        form.set_description(f"Hợp đồng cho: {prof.pronoun} {prof.expert_name}")
        form.set_color("#5865F2")

        form.add_input_field(
            "order_id",
            "Mã hợp đồng",
            placeholder="HD-2026-001",
        )
        form.add_input_field(
            "contract_date",
            "Ngày hợp đồng",
            placeholder="07/05/2026",
        )
        form.add_input_field(
            "program_code",
            "Mã dự án",
            placeholder="PROG-001",
        )
        form.add_input_field(
            "additional_information",
            "Thông tin thêm",
            placeholder="(nếu có)",
            options=InputFieldOption(textarea=True),
        )
        return form

    def _build_activity_form(self, existing_count: int = 0) -> InteractiveBuilder:
        """Build the interactive form for adding a contract activity."""
        next_num = existing_count + 1
        form = InteractiveBuilder(f"➕ Thêm hoạt động #{next_num}")
        form.set_description(f"Gợi ý mã: 1.{next_num}")
        form.set_color("#10B981")

        form.add_input_field(
            "activity_name",
            "Tên hoạt động (bao gồm mã)",
            placeholder="1.1 Phản biện độc lập",
        )
        form.add_input_field(
            "budget",
            "Vị trí trong hoạt động",
            placeholder="Chuyên gia phản biện",
        )
        form.add_input_field(
            "working_days",
            "Số ngày làm việc",
            placeholder="5",
        )
        form.add_input_field(
            "rate",
            "Rate (VNĐ/ngày)",
            placeholder="500000",
            options=InputFieldOption(type="number"),
        )
        return form

    def _format_expert(self, p: ExpertData) -> str:
        """Format a single expert record."""
        lines = [
            f"👤 **{p.pronoun} {p.expert_name}** (ID: {p.id})",
            f"   Quốc tịch: {p.nationality or '—'}",
            f"   Địa chỉ: {p.address or '—'}",
            f"   CCCD: {p.id_number or '—'}",
            f"   Ngày cấp: {format_date_vn(p.issued_date) if p.issued_date else '—'}",
            f"   Nơi cấp: {p.issued_place or '—'}",
            f"   Email: {p.email_address or '—'}",
            f"   SĐT: {p.phone or '—'}",
            f"   Ngân hàng: {p.bank_name or '—'} tại {p.bank_account or '—'}",
        ]
        return "\n".join(lines)

    def _format_expert_lookup_matches(self, experts: list[ExpertData]) -> str:
        """Format expert matches for user-facing disambiguation."""
        lines = [
            f"📋 Tìm thấy {len(experts)} chuyên gia trùng khớp. Hãy chọn đúng người bên dưới:"
        ]
        for expert in experts[:10]:
            lines.append(
                f"- {expert.pronoun} {expert.expert_name} | CCCD: {expert.id_number or '—'}"
            )
        if len(experts) > 10:
            lines.append("Hiển thị 10 kết quả đầu. Hãy nhập tên cụ thể hơn hoặc dùng CCCD.")
        return "\n".join(lines)

    def _build_expert_resolution_buttons(
        self, action: str, experts: list[ExpertData]
    ) -> list[MessageActionRow]:
        """Build buttons for ambiguous expert lookup."""
        rows: list[MessageActionRow] = []
        for expert in experts[:10]:
            rows.extend(
                self._build_buttons(
                    [
                        (
                            f"resolve_{action}:{expert.id}",
                            f"{expert.expert_name} | {expert.id_number or '—'}",
                            ButtonMessageStyle.PRIMARY,
                        )
                    ]
                )
            )
        rows.extend(
            self._build_buttons(
                [("cancel", "❌ Hủy", ButtonMessageStyle.SECONDARY)]
            )
        )
        return rows

    async def _resolve_single_expert(
        self, keyword: str | None
    ) -> tuple[ExpertData | None, list[ExpertData] | None, str | None]:
        """Resolve one expert from user input using CCCD or name."""
        if not keyword or not keyword.strip():
            return (
                None,
                None,
                "❌ Thiếu thông tin tìm kiếm. Hãy nhập CCCD hoặc tên chuyên gia.",
            )

        matches = await self.expert_service.resolve_experts(keyword)
        if not matches:
            return (
                None,
                None,
                f"❌ Không tìm thấy chuyên gia với từ khóa: `{keyword.strip()}`",
            )

        if len(matches) > 1:
            return None, matches, None

        return matches[0], None, None

    @command("*expert")
    async def handle_expert(
        self,
        message: Any,
        subcmd: str = None,
        rest: str = None,
    ) -> None:
        """Manage experts.

        Usage:
            *expert
            *expert list
            *expert add
            *expert edit <cccd|tên>
            *expert delete <cccd|tên>
            *expert find name <search_term>
            *expert find id <cccd_number>
        """
        if not subcmd:
            await self.reply_message(
                message,
                "📋 **Quản lý chuyên gia**\n\n"
                "Chọn thao tác ở trên, hoặc dùng trực tiếp:\n"
                "`*expert list` - Danh sách\n"
                "`*expert add` - Thêm mới\n"
                "`*expert edit <cccd|tên>` - Sửa\n"
                "`*expert delete <cccd|tên>` - Xóa\n"
                "`*expert find name <tên>` - Tìm theo tên\n"
                "`*expert find id <cccd>` - Tìm theo CCCD",
            )
            return

        if subcmd == "list":
            await self._handle_list(message)
        elif subcmd == "add":
            await self._handle_add(message)
        elif subcmd == "edit":
            await self._handle_edit(message, rest)
        elif subcmd == "delete":
            await self._handle_delete(message, rest)
        elif subcmd == "find":
            await self._handle_find(message, rest)
        else:
            await self.reply_message(
                message,
                f"❌ Lệnh con không hợp lệ: `{subcmd}`.\n"
                "Dùng `*expert` để xem danh sách lệnh.",
            )

    @command("*contract")
    async def handle_contract(
        self,
        message: Any,
        target: str = None,
        action: str = None,
        filter_key: str = None,
        rest: str = None,
    ) -> None:
        """Handle *contract expert list year <YYYY>."""
        if not target:
            await self._handle_contract_help(message)
            return

        if target != "expert" or action != "list" or filter_key != "year":
            await self.reply_message(
                message,
                "❌ Cú pháp không hợp lệ. Dùng: `*contract expert list year <YYYY>`",
            )
            return

        if not self.contract_service:
            await self.reply_message(message, "❌ Contract service không khả dụng.")
            return

        try:
            year = int((rest or "").strip())
        except ValueError:
            await self.reply_message(
                message,
                "❌ Năm không hợp lệ. Dùng: `*contract expert list year <YYYY>`",
            )
            return

        contracts = await self.contract_service.get_contracts_by_year(year)
        if not contracts:
            await self.reply_message(
                message,
                f"📋 Không có hợp đồng chuyên gia nào trong năm **{year}**.",
            )
            return

        lines = [f"📋 **Danh sách hợp đồng chuyên gia năm {year}**\n"]
        for contract in contracts:
            expert = await self.expert_service.get_expert_by_id(contract.expert_id)
            activities = await self.contract_service.get_activities_by_contract_id(contract.id)
            expert_name = (
                f"{expert.pronoun} {expert.expert_name}" if expert else f"Chuyên gia #{contract.expert_id}"
            )
            lines.append(
                f"• **{contract.order_id}** ({contract.dd:02d}/{contract.mm:02d}/{contract.yyyy})\n"
                f"  Chuyên gia: {expert_name}\n"
                f"  Dự án: {contract.project_name or contract.abbreviated_project or '—'}\n"
                f"  Hoạt động: {len(activities)} | Tổng: {format_currency_vn(contract.total_amount)} | Thực nhận: {format_currency_vn(contract.final_amount)}"
            )
            lines.append("")

        await self.reply_message(message, "\n".join(lines))

    async def _handle_contract_help(self, message: Any) -> None:
        """Show help message for contract commands."""
        await self.reply_message(
            message,
            "📋 **Quản lý hợp đồng**\n\n"
            "**Lệnh:**\n"
            "• `*contract expert list year <YYYY>` — Danh sách hợp đồng chuyên gia theo năm",
        )

    async def _handle_list(self, message: Any) -> None:
        experts = await self.expert_service.list_all()
        if not experts:
            await self.reply_message(
                message, "📋 Chưa có chuyên gia nào trong hệ thống."
            )
            return

        form = InteractiveBuilder("📋 Danh sách chuyên gia")
        form.set_color("#10B981")
        form.set_description(f"Tổng cộng: {len(experts)} chuyên gia")

        for p in experts:
            form.add_field(
                f"{p.id}. {p.pronoun} {p.expert_name}",
                f"CCCD: {p.id_number or '—'} | SĐT: {p.phone or '—'}",
            )

        await self.reply_message(
            message,
            f"📋 **Danh sách {len(experts)} chuyên gia:**",
            embeds=[InteractiveMessageProps(**form.build())],
        )

    async def _handle_add(self, message: Any) -> None:
        """Send interactive form to add a new expert."""
        form = self._build_add_form()
        buttons = self._build_form_buttons()

        await self.reply_message(
            message,
            "📝 Vui lòng điền thông tin chuyên gia bên dưới:",
            embeds=[InteractiveMessageProps(**form.build())],
            components=buttons,
        )

    async def _handle_edit(self, message: Any, rest: str | None) -> None:
        """Send interactive form to edit an expert."""
        if not rest:
            # Show list first
            experts = await self.expert_service.list_all()
            if not experts:
                await self.reply_message(message, "📋 Chưa có chuyên gia nào để sửa.")
                return

            form = InteractiveBuilder("✏️ Chọn chuyên gia cần sửa")
            form.set_description("Chọn chuyên gia muốn chỉnh sửa")
            form.set_color("#F59E0B")

            form.add_radio_field(
                "prof_id",
                "Chuyên gia",
                options=[
                    RadioFieldOption(
                        label=f"{p.id}. {p.pronoun} {p.expert_name}",
                        value=str(p.id),
                        description=f"CCCD: {p.id_number or '—'}",
                    )
                    for p in experts[:10]
                ],
                description="Chọn chuyên gia (tối đa 10)",
            )

            await self.reply_message(
                message,
                "📋 Danh sách chuyên gia (hiển thị tối đa 10):",
                embeds=[InteractiveMessageProps(**form.build())],
                components=self._build_buttons(
                    [("select_prof", "📝 Chọn", ButtonMessageStyle.PRIMARY)]
                ),
            )
            return

        existing, matches, error_message = await self._resolve_single_expert(rest)
        if error_message:
            await self.reply_message(message, error_message)
            return
        if matches:
            await self.reply_message(
                message,
                self._format_expert_lookup_matches(matches),
                components=self._build_expert_resolution_buttons("edit", matches),
            )
            return

        form = self._build_edit_form(existing)

        await self.reply_message(
            message,
            f"✏️ Đang sửa thông tin chuyên gia: **{existing.pronoun} {existing.expert_name}**",
            embeds=[InteractiveMessageProps(**form.build())],
            components=self._build_edit_buttons(existing.id),
        )

    async def _handle_delete(self, message: Any, rest: str | None) -> None:
        """Send confirmation to delete an expert."""
        if not rest:
            await self.reply_message(
                message,
                "❌ Thiếu thông tin.\nCách dùng: `*expert delete <cccd|tên>`",
            )
            return

        existing, matches, error_message = await self._resolve_single_expert(rest)
        if error_message:
            await self.reply_message(message, error_message)
            return
        if matches:
            await self.reply_message(
                message,
                self._format_expert_lookup_matches(matches),
                components=self._build_expert_resolution_buttons("delete", matches),
            )
            return

        form = InteractiveBuilder("⚠️ Xác nhận xóa")
        form.set_description(
            f"Bạn có chắc chắn muốn xóa chuyên gia:\n"
            f"**{existing.pronoun} {existing.expert_name}** (ID: {existing.id})\n"
            f"CCCD: {existing.id_number or '—'}"
        )
        form.set_color("#EF4444")

        await self.reply_message(
            message,
            f"⚠️ Xác nhận xóa chuyên gia: **{existing.pronoun} {existing.expert_name}**",
            embeds=[InteractiveMessageProps(**form.build())],
            components=self._build_delete_buttons(existing.id),
        )

    async def _handle_find(self, message: Any, rest: str | None) -> None:
        if not rest:
            await self.reply_message(
                message,
                "❌ Thiếu thông tin tìm kiếm.\n"
                "Cách dùng:\n"
                "  `*expert find name <tên>` - Tìm theo tên\n"
                "  `*expert find id <cccd>` - Tìm theo CCCD",
            )
            return

        parts = rest.strip().split(maxsplit=1)
        if len(parts) < 2 or not parts[1].strip():
            await self.reply_message(message, "❌ Thiếu từ khóa tìm kiếm.")
            return

        search_type = parts[0].lower()
        keyword = parts[1].strip()

        if search_type == "name":
            results = await self.expert_service.find_by_name(keyword)
            if not results:
                await self.reply_message(
                    message,
                    f"❌ Không tìm thấy chuyên gia nào với tên chứa: `{keyword}`",
                )
                return

            for p in results:
                buttons = self._build_find_buttons(p.id)
                await self.reply_message(
                    message,
                    self._format_expert(p),
                    components=buttons,
                )

        elif search_type == "id":
            result = await self.expert_service.find_by_id_number(keyword)
            if not result:
                await self.reply_message(
                    message, f"❌ Không tìm thấy chuyên gia với CCCD: `{keyword}`"
                )
                return

            buttons = self._build_find_buttons(result.id)
            await self.reply_message(
                message,
                self._format_expert(result),
                components=buttons,
            )
        else:
            await self.reply_message(
                message,
                f"❌ Loại tìm kiếm không hợp lệ: `{search_type}`. Dùng `name` hoặc `id`.",
            )

    async def handle_button_click(
        self, event: realtime_pb2.MessageButtonClicked
    ) -> None:
        """Handle button click events from interactive forms."""
        try:
            self.logger.info(
                "Button click: button_id=%s, message_id=%d, user_id=%d",
                event.button_id,
                event.message_id,
                event.user_id,
            )

            # Parse extra_data for form values
            extra_data = form_tracker.parse_extra_data(event.extra_data)

            if event.button_id == "cancel":
                await self._handle_cancel(event)
                return

            if event.button_id.startswith("delete_confirm:"):
                prof_id = int(event.button_id.split(":")[1])
                await self._handle_delete_confirm(event, prof_id)
                return

            if event.button_id.startswith("resolve_edit:"):
                prof_id = int(event.button_id.split(":")[1])
                await self._handle_resolve_edit(event, prof_id)
                return

            if event.button_id.startswith("resolve_delete:"):
                prof_id = int(event.button_id.split(":")[1])
                await self._handle_resolve_delete(event, prof_id)
                return

            if event.button_id.startswith("save_edit:"):
                prof_id = int(event.button_id.split(":")[1])
                await self._handle_save_edit(event, prof_id, extra_data)
                return

            if event.button_id == "save" or event.button_id == "save_edit":
                await self._handle_save(event, extra_data)
                return

            if event.button_id == "select_prof":
                await self._handle_select_prof(event, extra_data)
                return

            # Contract-related buttons
            if event.button_id.startswith("create_contract:"):
                prof_id = int(event.button_id.split(":")[1])
                await self._handle_create_contract_button(event, prof_id)
                return

            if event.button_id.startswith("list_contracts:"):
                prof_id = int(event.button_id.split(":")[1])
                await self._handle_list_contracts_button(event, prof_id)
                return

            if event.button_id.startswith("save_contract:"):
                prof_id = int(event.button_id.split(":")[1])
                await self._handle_save_contract(event, prof_id, extra_data)
                return

            if event.button_id.startswith("save_activity:"):
                contract_id = int(event.button_id.split(":")[1])
                await self._handle_save_activity(event, contract_id, extra_data)
                return

            if event.button_id.startswith("add_more_activity:"):
                contract_id = int(event.button_id.split(":")[1])
                await self._handle_add_more_activity(event, contract_id)
                return

            if event.button_id.startswith("finalize_contract:"):
                contract_id = int(event.button_id.split(":")[1])
                await self._handle_finalize_contract(event, contract_id)
                return

            if event.button_id.startswith("edit_contract:"):
                contract_id = int(event.button_id.split(":")[1])
                await self._handle_edit_contract_button(event, contract_id)
                return

            if event.button_id.startswith("view_contract:"):
                contract_id = int(event.button_id.split(":")[1])
                await self._handle_view_contract(event, contract_id)
                return

            if event.button_id.startswith("delete_contract_confirm:"):
                contract_id = int(event.button_id.split(":")[1])
                await self._handle_delete_contract_confirm(event, contract_id)
                return

            if event.button_id.startswith("export_word:"):
                contract_id = int(event.button_id.split(":")[1])
                await self._handle_export_word(event, contract_id)
                return

            if event.button_id.startswith("acceptance_report:"):
                contract_id = int(event.button_id.split(":")[1])
                await self._handle_acceptance_report(event, contract_id)
                return

            if event.button_id.startswith("export_acceptance:"):
                contract_id = int(event.button_id.split(":")[1])
                await self._handle_export_acceptance(event, contract_id, extra_data)
                return

            # Button not handled by this handler - let other handlers try
            return

        except Exception as e:
            self.logger.error("Error handling button click: %s", e, exc_info=True)
            await self.edit_message(
                event.channel_id,
                event.message_id,
                f"❌ Lỗi xử lý: {e}",
                components=[],
            )

    async def _handle_cancel(self, event: realtime_pb2.MessageButtonClicked) -> None:
        await self.edit_message(
            event.channel_id,
            event.message_id,
            "❌ Đã hủy thao tác.",
            components=[],
        )

    async def _handle_delete_confirm(
        self, event: realtime_pb2.MessageButtonClicked, prof_id: int
    ) -> None:
        success = await self.expert_service.delete_expert(prof_id)
        if success:
            await self.edit_message(
                event.channel_id,
                event.message_id,
                f"✅ Đã xóa chuyên gia ID {prof_id}.",
                components=[],
            )
        else:
            await self.edit_message(
                event.channel_id,
                event.message_id,
                "❌ Không thể xóa chuyên gia.",
                components=[],
            )

    async def _handle_resolve_edit(
        self, event: realtime_pb2.MessageButtonClicked, prof_id: int
    ) -> None:
        """Continue edit flow after disambiguation."""
        existing = await self.expert_service.get_active_expert_by_id(prof_id)
        if not existing:
            await self.edit_message(
                event.channel_id,
                event.message_id,
                "❌ Không tìm thấy chuyên gia.",
                components=[],
            )
            return

        form = self._build_edit_form(existing)
        await self.edit_message(
            event.channel_id,
            event.message_id,
            f"✏️ Đang sửa thông tin chuyên gia: **{existing.pronoun} {existing.expert_name}**",
            embeds=[InteractiveMessageProps(**form.build())],
            components=self._build_edit_buttons(existing.id),
        )

    async def _handle_resolve_delete(
        self, event: realtime_pb2.MessageButtonClicked, prof_id: int
    ) -> None:
        """Continue delete flow after disambiguation."""
        existing = await self.expert_service.get_active_expert_by_id(prof_id)
        if not existing:
            await self.edit_message(
                event.channel_id,
                event.message_id,
                "❌ Không tìm thấy chuyên gia.",
                components=[],
            )
            return

        form = InteractiveBuilder("⚠️ Xác nhận xóa")
        form.set_description(
            f"Bạn có chắc chắn muốn xóa chuyên gia:\n"
            f"**{existing.pronoun} {existing.expert_name}** (ID: {existing.id})\n"
            f"CCCD: {existing.id_number or '—'}"
        )
        form.set_color("#EF4444")

        await self.edit_message(
            event.channel_id,
            event.message_id,
            f"⚠️ Xác nhận xóa chuyên gia: **{existing.pronoun} {existing.expert_name}**",
            embeds=[InteractiveMessageProps(**form.build())],
            components=self._build_delete_buttons(existing.id),
        )

    async def _handle_save(
        self, event: realtime_pb2.MessageButtonClicked, extra_data: dict[str, Any]
    ) -> None:
        """Handle save button from add form."""
        try:
            expert_name = extra_data.get("expert_name", "").strip()
            if not expert_name:
                await self.edit_message(
                    event.channel_id,
                    event.message_id,
                    "❌ Thiếu tên chuyên gia.",
                    components=[],
                )
                return

            pronoun = extra_data.get("pronoun", "Ông").strip()
            id_number = extra_data.get("id_number", "").strip() or None

            issued_date = None
            if extra_data.get("issued_date"):
                try:
                    d, m, y = extra_data["issued_date"].split("/")
                    issued_date = date_type(int(y), int(m), int(d))
                except (ValueError, IndexError):
                    pass

            data = ExpertData(
                id=0,
                pronoun=pronoun,
                expert_name=expert_name,
                nationality=extra_data.get("nationality") or None,
                address=extra_data.get("address") or None,
                id_number=id_number,
                issued_date=issued_date,
                issued_place=extra_data.get("issued_place") or None,
                email_address=extra_data.get("email_address") or None,
                phone=extra_data.get("phone") or None,
                bank_account=extra_data.get("bank_account") or None,
                bank_name=extra_data.get("bank_name") or None,
            )

            created = await self.expert_service.create_expert(data)

            # Clear form data
            form_tracker.clear_form_data(str(event.message_id))

            await self.edit_message(
                event.channel_id,
                event.message_id,
                f"✅ Đã thêm chuyên gia:\n"
                f"ID: {created.id}\n"
                f"{created.pronoun} {created.expert_name}\n"
                f"CCCD: {created.id_number or '—'}",
                components=[],
            )
        except Exception as e:
            self.logger.error("Error saving expert: %s", e)
            await self.edit_message(
                event.channel_id,
                event.message_id,
                f"❌ Lỗi lưu chuyên gia: {e}",
                components=[],
            )

    async def _handle_save_edit(
        self,
        event: realtime_pb2.MessageButtonClicked,
        prof_id: int,
        extra_data: dict[str, Any],
    ) -> None:
        """Handle save button from edit form."""
        existing = await self.expert_service.get_active_expert_by_id(prof_id)
        if not existing:
            await self.edit_message(
                event.channel_id,
                event.message_id,
                "❌ Không tìm thấy chuyên gia.",
                components=[],
            )
            return

        expert_name = extra_data.get("expert_name", existing.expert_name).strip()
        if not expert_name:
            await self.edit_message(
                event.channel_id,
                event.message_id,
                "❌ Tên chuyên gia không được để trống.",
                components=[],
            )
            return

        pronoun = extra_data.get("pronoun", existing.pronoun).strip()
        id_number = extra_data.get("id_number", existing.id_number).strip() or None

        issued_date = existing.issued_date
        if extra_data.get("issued_date"):
            try:
                d, m, y = extra_data["issued_date"].split("/")
                issued_date = date_type(int(y), int(m), int(d))
            except (ValueError, IndexError):
                pass

        data = ExpertData(
            id=existing.id,
            pronoun=pronoun,
            expert_name=expert_name,
            nationality=extra_data.get("nationality") or existing.nationality,
            address=extra_data.get("address") or existing.address,
            id_number=id_number or existing.id_number,
            issued_date=issued_date,
            issued_place=extra_data.get("issued_place") or existing.issued_place,
            email_address=extra_data.get("email_address") or existing.email_address,
            phone=extra_data.get("phone") or existing.phone,
            bank_account=extra_data.get("bank_account") or existing.bank_account,
            bank_name=extra_data.get("bank_name") or existing.bank_name,
        )

        updated = await self.expert_service.update_expert(prof_id, data)
        if updated:
            # Clear form data
            form_tracker.clear_form_data(str(event.message_id))

            await self.edit_message(
                event.channel_id,
                event.message_id,
                f"✅ Đã cập nhật chuyên gia:\n"
                f"ID: {updated.id}\n"
                f"{updated.pronoun} {updated.expert_name}",
                components=[],
            )
        else:
            await self.edit_message(
                event.channel_id,
                event.message_id,
                "❌ Không thể cập nhật chuyên gia.",
                components=[],
            )

    async def _handle_select_prof(
        self, event: realtime_pb2.MessageButtonClicked, extra_data: dict[str, Any]
    ) -> None:
        """Handle expert selection from list."""
        prof_id_str = extra_data.get("prof_id")
        if not prof_id_str:
            await self.edit_message(
                event.channel_id,
                event.message_id,
                "❌ Chưa chọn chuyên gia.",
                components=[],
            )
            return

        try:
            prof_id = int(prof_id_str)
        except ValueError:
            await self.edit_message(
                event.channel_id, event.message_id, "❌ ID không hợp lệ.", components=[]
            )
            return

        existing = await self.expert_service.get_active_expert_by_id(prof_id)
        if not existing:
            await self.edit_message(
                event.channel_id,
                event.message_id,
                "❌ Không tìm thấy chuyên gia.",
                components=[],
            )
            return

        form = self._build_edit_form(existing)

        await self.edit_message(
            event.channel_id,
            event.message_id,
            f"✏️ Đang sửa thông tin: **{existing.pronoun} {existing.expert_name}**",
            embeds=[InteractiveMessageProps(**form.build())],
            components=self._build_edit_buttons(prof_id),
        )

    # Contract handlers
    async def _handle_create_contract_button(
        self, event: realtime_pb2.MessageButtonClicked, prof_id: int
    ) -> None:
        """Handle create contract button click."""
        if not self.contract_service:
            await self.edit_message(
                event.channel_id,
                event.message_id,
                "❌ Contract service không khả dụng.",
                components=[],
            )
            return

        prof = await self.expert_service.get_active_expert_by_id(prof_id)
        if not prof:
            await self.edit_message(
                event.channel_id,
                event.message_id,
                "❌ Không tìm thấy chuyên gia.",
                components=[],
            )
            return

        form = self._build_contract_form(prof)
        await self.edit_message(
            event.channel_id,
            event.message_id,
            f"📝 Tạo hợp đồng cho: **{prof.pronoun} {prof.expert_name}**",
            embeds=[InteractiveMessageProps(**form.build())],
            components=self._build_contract_action_buttons(prof_id),
        )

    async def _handle_save_contract(
        self,
        event: realtime_pb2.MessageButtonClicked,
        prof_id: int,
        extra_data: dict[str, Any],
    ) -> None:
        """Handle save contract form submission."""
        if not self.contract_service:
            await self.edit_message(
                event.channel_id,
                event.message_id,
                "❌ Contract service không khả dụng.",
                components=[],
            )
            return

        prof = await self.expert_service.get_active_expert_by_id(prof_id)
        if not prof:
            await self.edit_message(
                event.channel_id,
                event.message_id,
                "❌ Chuyên gia không còn hoạt động hoặc không tồn tại.",
                components=[],
            )
            return

        try:
            order_id = extra_data.get("order_id", "").strip()
            if not order_id:
                await self.edit_message(
                    event.channel_id,
                    event.message_id,
                    "❌ Thiếu mã hợp đồng.",
                    components=[],
                )
                return

            try:
                contract_date_str = extra_data.get("contract_date", "").strip()
                d, m, y = contract_date_str.split("/")
                dd, mm, yyyy = int(d), int(m), int(y)
            except (ValueError, TypeError, IndexError):
                await self.edit_message(
                    event.channel_id,
                    event.message_id,
                    "❌ Ngày hợp đồng không hợp lệ. Định dạng: dd/mm/yyyy",
                    components=[],
                )
                return

            program_code = normalize_program_code(extra_data.get("program_code", ""))
            if not program_code:
                await self.edit_message(
                    event.channel_id,
                    event.message_id,
                    "❌ Thiếu mã chương trình.",
                    components=[],
                )
                return

            program_id = await self.contract_service.resolve_program_code(program_code)
            if not program_id:
                await self.edit_message(
                    event.channel_id,
                    event.message_id,
                    f"❌ Không tìm thấy chương trình với mã '{program_code}'.",
                    components=[],
                )
                return

            abbreviated_project = program_code
            duplicate_contract = (
                await self.contract_service.has_contract_order_in_project(
                    order_id,
                    abbreviated_project,
                )
            )
            if duplicate_contract:
                await self.edit_message(
                    event.channel_id,
                    event.message_id,
                    f"❌ Số hợp đồng **{order_id}** đã tồn tại trong dự án **{abbreviated_project}**.",
                    components=[],
                )
                return

            contract_data = ContractData(
                id=0,
                order_id=order_id,
                dd=dd,
                mm=mm,
                yyyy=yyyy,
                abbreviated_project=abbreviated_project,
                additional_information=extra_data.get("additional_information"),
                expert_id=prof_id,
                program_id=program_id,
            )

            created = await self.contract_service.create_contract(contract_data)

            # Clear form data
            form_tracker.clear_form_data(str(event.message_id))

            # Confirm contract creation (edit existing message, remove form)
            await self.edit_message(
                event.channel_id,
                event.message_id,
                f"✅ Đã tạo hợp đồng **{created.order_id}**.",
                components=[],
            )

            # Send activity form as a NEW message to avoid SDK merging old form data
            send_key = f"send_activity_form:{event.message_id}"
            if send_key not in self._processed_activity_submits:
                self._processed_activity_submits.add(send_key)
                form = self._build_activity_form(existing_count=0)
                channel = await self.client.channels.fetch(event.channel_id)
                await channel.send(
                    content=ChannelMessageContent(
                        t="➕ Thêm hoạt động đầu tiên:",
                        embed=[InteractiveMessageProps(**form.build())],
                        components=self._build_activity_buttons(created.id),
                    ),
                )
        except Exception as e:
            self.logger.error("Error saving contract: %s", e, exc_info=True)
            await self.edit_message(
                event.channel_id,
                event.message_id,
                f"❌ Lỗi tạo hợp đồng: {e}",
                components=[],
            )

    async def _handle_save_activity(
        self,
        event: realtime_pb2.MessageButtonClicked,
        contract_id: int,
        extra_data: dict[str, Any],
    ) -> None:
        """Handle save activity form submission."""
        if not self.contract_service:
            await self.edit_message(
                event.channel_id,
                event.message_id,
                "❌ Contract service không khả dụng.",
                components=[],
            )
            return

        try:
            submit_key = f"{event.message_id}:{contract_id}"
            if submit_key in self._processed_activity_submits:
                await self.edit_message(
                    event.channel_id,
                    event.message_id,
                    "✅ Hoạt động đã được lưu trước đó.",
                    components=[],
                )
                return

            contract = await self.contract_service.get_contract_by_id(contract_id)
            if not contract:
                await self.edit_message(
                    event.channel_id,
                    event.message_id,
                    "❌ Không tìm thấy hợp đồng.",
                    components=[],
                )
                return

            # SDK merges all previous form data; activity_name is from the activity form.
            activity_name = extra_data.get("activity_name", "").strip()
            budget = extra_data.get("budget", "").strip()

            try:
                working_days = float(str(extra_data.get("working_days", 0)).strip())
            except (ValueError, TypeError):
                await self.edit_message(
                    event.channel_id,
                    event.message_id,
                    "❌ Số ngày làm việc không hợp lệ.",
                    components=[],
                )
                return

            if working_days <= 0:
                await self.edit_message(
                    event.channel_id,
                    event.message_id,
                    "❌ Số ngày làm việc phải lớn hơn 0.",
                    components=[],
                )
                return

            if not activity_name:
                await self.edit_message(
                    event.channel_id,
                    event.message_id,
                    "❌ Thiếu tên hoạt động.",
                    components=[],
                )
                return

            try:
                rate = float(
                    extra_data.get("rate", "0")
                    .strip()
                    .replace(".", "")
                    .replace(",", "")
                )
            except (ValueError, TypeError):
                rate = 0
            real_amount = working_days * rate

            # Generate sequential activity_number (e.g., 01, 02, 03...)
            existing_activities = await self.contract_service.get_activities_by_contract_id(contract_id)
            next_num = len(existing_activities) + 1
            activity_number = f"{next_num:02d}"

            activity_data = ActivityData(
                id=0,
                activity_number=activity_number,
                activity_name=activity_name,
                budget=budget,
                working_days=working_days,
                rate=rate,
                real_amount=real_amount,
                contract_id=contract_id,
            )

            await self.contract_service.add_activity(contract_id, activity_data)
            self._processed_activity_submits.add(submit_key)

            # Clear form data
            form_tracker.clear_form_data(str(event.message_id))

            await self.edit_message(
                event.channel_id,
                event.message_id,
                f"✅ Đã thêm hoạt động: **{activity_name}**\n"
                f"Số ngày: {self._format_working_days(working_days)} | Rate: {format_currency_vn(rate)} | Thành tiền: {format_currency_vn(real_amount)}\n\n"
                "Tiếp tục thêm hoạt động hoặc hoàn tất?",
                components=self._build_after_activity_buttons(contract_id),
            )
        except Exception as e:
            self.logger.error("Error saving activity: %s", e, exc_info=True)
            await self.edit_message(
                event.channel_id,
                event.message_id,
                f"❌ Lỗi thêm hoạt động: {e}",
                components=[],
            )

    async def _handle_add_more_activity(
        self, event: realtime_pb2.MessageButtonClicked, contract_id: int
    ) -> None:
        """Handle add more activity button."""
        if not self.contract_service:
            await self.edit_message(
                event.channel_id,
                event.message_id,
                "❌ Contract service không khả dụng.",
                components=[],
            )
            return

        contract = await self.contract_service.get_contract_by_id(contract_id)
        if not contract:
            await self.edit_message(
                event.channel_id,
                event.message_id,
                "❌ Không tìm thấy hợp đồng.",
                components=[],
            )
            return

        prof = await self.expert_service.get_expert_by_id(contract.expert_id)
        if not prof:
            await self.edit_message(
                event.channel_id,
                event.message_id,
                "❌ Không tìm thấy chuyên gia.",
                components=[],
            )
            return

        activities = await self.contract_service.get_activities_by_contract_id(
            contract_id
        )
        # Confirm previous activity saved (edit existing message, remove form)
        await self.edit_message(
            event.channel_id,
            event.message_id,
            "✅ Đã lưu hoạt động.",
            components=[],
        )

        # Send new activity form as a NEW message to avoid SDK merging old form data
        send_key = f"send_activity_form:{event.message_id}"
        if send_key not in self._processed_activity_submits:
            self._processed_activity_submits.add(send_key)
            form = self._build_activity_form(existing_count=len(activities))
            channel = await self.client.channels.fetch(event.channel_id)
            await channel.send(
                content=ChannelMessageContent(
                    t="➕ Thêm hoạt động mới:",
                    embed=[InteractiveMessageProps(**form.build())],
                    components=self._build_activity_buttons(contract_id),
                ),
            )

    async def _handle_finalize_contract(
        self, event: realtime_pb2.MessageButtonClicked, contract_id: int
    ) -> None:
        """Handle finalize contract button."""
        if not self.contract_service:
            await self.edit_message(
                event.channel_id,
                event.message_id,
                "❌ Contract service không khả dụng.",
                components=[],
            )
            return

        contract = await self.contract_service.finalize_contract(contract_id)
        if not contract:
            await self.edit_message(
                event.channel_id,
                event.message_id,
                "❌ Không thể hoàn tất hợp đồng.",
                components=[],
            )
            return

        activities = await self.contract_service.get_activities_by_contract_id(
            contract_id
        )

        summary = [
            f"✅ **Hợp đồng {contract.order_id} đã hoàn tất!**\n",
            f"📋 Dự án: {contract.project_name or '—'}",
            f"📅 Ngày: {contract.dd}/{contract.mm}/{contract.yyyy}",
            f"📅 Hết hạn: {format_date_vn(contract.end_date) if contract.end_date else '—'}\n",
            f"**Danh sách hoạt động ({len(activities)}):**",
        ]

        for act in activities:
            summary.append(
                f"  • {act.activity_number}: {act.activity_name} - {self._format_working_days(act.working_days)} ngày × {format_currency_vn(act.rate)} = {format_currency_vn(act.real_amount)}"
            )

        summary.extend(
            [
                f"\n💰 **Tổng chi phí:** {format_currency_vn(contract.total_amount)}",
                f"📊 **Thuế TNCN (10%):** {format_currency_vn(contract.total_amount * contract.tax)}",
                f"💵 **Thực nhận:** {format_currency_vn(contract.final_amount)}",
                f"🔤 **Bằng chữ:** {number_to_vietnamese_text(contract.final_amount)}",
            ]
        )

        await self.edit_message(
            event.channel_id,
            event.message_id,
            "\n".join(summary),
            components=self._build_finalized_buttons(contract_id),
        )

    async def _handle_list_contracts_button(
        self, event: realtime_pb2.MessageButtonClicked, prof_id: int
    ) -> None:
        """Handle list contracts button."""
        if not self.contract_service:
            await self.edit_message(
                event.channel_id,
                event.message_id,
                "❌ Contract service không khả dụng.",
                components=[],
            )
            return

        contracts = await self.contract_service.get_contracts_by_expert_id(prof_id)
        if not contracts:
            await self.edit_message(
                event.channel_id,
                event.message_id,
                "📋 Chưa có hợp đồng nào cho chuyên gia này.",
                components=[],
            )
            return

        prof = await self.expert_service.get_expert_by_id(prof_id)
        expert_title = (
            f"{prof.pronoun} {prof.expert_name}" if prof else f"chuyên gia #{prof_id}"
        )
        summary = [f"📋 **Danh sách hợp đồng: {expert_title}**\n"]

        for c in contracts:
            activities = await self.contract_service.get_activities_by_contract_id(c.id)
            summary.append(
                f"• **{c.order_id}** ({c.dd}/{c.mm}/{c.yyyy})\n"
                f"  Dự án: {c.project_name or '—'}\n"
                f"  Hoạt động: {len(activities)} | Tổng: {format_currency_vn(c.total_amount)} | Thực nhận: {format_currency_vn(c.final_amount)}"
            )
            summary.append("")

        await self.edit_message(
            event.channel_id,
            event.message_id,
            "\n".join(summary),
            components=self._build_contract_list_rows(
                prof_id, contracts, allow_create=prof is not None
            ),
        )

    async def _handle_view_contract(
        self, event: realtime_pb2.MessageButtonClicked, contract_id: int
    ) -> None:
        """View detailed contract info by contract ID."""
        if not self.contract_service:
            await self.edit_message(
                event.channel_id,
                event.message_id,
                "❌ Contract service không khả dụng.",
                components=[],
            )
            return

        contract = await self.contract_service.get_contract_by_id(contract_id)
        if not contract:
            await self.edit_message(
                event.channel_id,
                event.message_id,
                "❌ Không tìm thấy hợp đồng.",
                components=[],
            )
            return

        activities = await self.contract_service.get_activities_by_contract_id(
            contract_id
        )
        expt = await self.expert_service.get_expert_by_id(contract.expert_id)

        lines = [
            f"📄 **Chi tiết hợp đồng: {contract.order_id}**\n",
            f"👤 Chuyên gia: **{expt.pronoun} {expt.expert_name}** (ID: {expt.id})"
            if expt
            else "👤 Chuyên gia: —",
            f"📅 Ngày: {contract.dd}/{contract.mm}/{contract.yyyy}",
            f"📋 Mã chương trình: {contract.abbreviated_project or '—'}",
            f"🏗️ Dự án: {contract.project_name or '—'}",
            f"📅 Hết hạn: {format_date_vn(contract.end_date) if contract.end_date else '—'}",
            f"🎯 Mục đích: {contract.activity_purpose or '—'}",
            f"📝 Tóm tắt: {contract.summary_activities or '—'}",
            f"💬 Thông tin thêm: {contract.additional_information or '—'}\n",
            f"**Hoạt động ({len(activities)}):**",
        ]

        for act in activities:
            lines.append(
                f"  • {act.activity_number}: {act.activity_name} — {self._format_working_days(act.working_days)} ngày × {format_currency_vn(act.rate)} = {format_currency_vn(act.real_amount)}"
            )

        lines.extend(
            [
                f"\n💰 **Tổng chi phí:** {format_currency_vn(contract.total_amount)}",
                f"📊 **Thuế TNCN (10%):** {format_currency_vn(contract.total_amount * contract.tax)}",
                f"💵 **Thực nhận:** {format_currency_vn(contract.final_amount)}",
                f"🔤 **Bằng chữ:** {number_to_vietnamese_text(contract.final_amount)}",
            ]
        )

        # Buttons: export word, acceptance report, edit, delete, back to list
        btn_rows = [
            self._build_buttons(
                [
                    (
                        f"export_word:{contract_id}",
                        "📄 Xuất HĐ",
                        ButtonMessageStyle.SUCCESS,
                    ),
                    (
                        f"acceptance_report:{contract_id}",
                        "✅ Nghiệm thu",
                        ButtonMessageStyle.PRIMARY,
                    ),
                ]
            ),
            self._build_buttons(
                [
                    (
                        f"edit_contract:{contract_id}",
                        "✏️ Sửa",
                        ButtonMessageStyle.PRIMARY,
                    ),
                    (
                        f"delete_contract_confirm:{contract_id}",
                        "🗑️ Xóa",
                        ButtonMessageStyle.DANGER,
                    ),
                ]
            ),
            self._build_buttons(
                [
                    (
                        f"list_contracts:{contract.expert_id}",
                        "⬅️ Quay lại danh sách",
                        ButtonMessageStyle.SECONDARY,
                    ),
                ]
            ),
        ]

        await self.edit_message(
            event.channel_id,
            event.message_id,
            "\n".join(lines),
            components=[row for r in btn_rows for row in r],
        )

    async def _handle_edit_contract_button(
        self, event: realtime_pb2.MessageButtonClicked, contract_id: int
    ) -> None:
        """Handle edit contract button."""
        await self.edit_message(
            event.channel_id,
            event.message_id,
            "⚠️ Chức năng sửa hợp đồng đang được phát triển.",
            components=[],
        )

    async def _handle_delete_contract_confirm(
        self, event: realtime_pb2.MessageButtonClicked, contract_id: int
    ) -> None:
        """Handle delete contract confirmation."""
        if not self.contract_service:
            await self.edit_message(
                event.channel_id,
                event.message_id,
                "❌ Contract service không khả dụng.",
                components=[],
            )
            return

        success = await self.contract_service.delete_contract(contract_id)
        if success:
            await self.edit_message(
                event.channel_id,
                event.message_id,
                f"✅ Đã xóa hợp đồng ID {contract_id}.",
                components=[],
            )
        else:
            await self.edit_message(
                event.channel_id,
                event.message_id,
                "❌ Không thể xóa hợp đồng.",
                components=[],
            )

    async def _handle_export_word(
        self, event: realtime_pb2.MessageButtonClicked, contract_id: int
    ) -> None:
        """Handle export Word document button."""
        if not self.contract_service or not self.word_export_service:
            await self.edit_message(
                event.channel_id,
                event.message_id,
                "❌ Service không khả dụng.",
                components=[],
            )
            return

        try:
            # Get contract data
            contract = await self.contract_service.get_contract_by_id(contract_id)
            if not contract:
                await self.edit_message(
                    event.channel_id,
                    event.message_id,
                    "❌ Không tìm thấy hợp đồng.",
                    components=[],
                )
                return

            # Get expert data
            prof = await self.expert_service.get_expert_by_id(contract.expert_id)
            if not prof:
                await self.edit_message(
                    event.channel_id,
                    event.message_id,
                    "❌ Không tìm thấy chuyên gia.",
                    components=[],
                )
                return

            # Get activities
            activities = await self.contract_service.get_activities_by_contract_id(
                contract_id
            )

            # Generate output filename
            import os

            output_dir = "exports"
            os.makedirs(output_dir, exist_ok=True)
            output_filename = (
                f"HDCG_{contract.order_id}_{prof.expert_name.replace(' ', '_')}.docx"
            )
            output_path = os.path.join(output_dir, output_filename)

            # Export to Word
            self.word_export_service.export_contract(
                contract, prof, activities, output_path
            )

            # Try upload to S3 if configured, fallback to Mezon upload
            file_url = None
            if self.s3_upload_service:
                try:
                    file_url = self.s3_upload_service.upload_file(
                        file_path=output_path,
                        object_name=output_filename,
                        content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    )
                except Exception as e:
                    self.logger.warning("S3 upload failed, trying Mezon upload: %s", e)

            # Fallback to Mezon upload if S3 failed or not configured
            if not file_url:
                upload_result = await self.client.upload_file(
                    file_path=output_path,
                    filename=output_filename,
                    content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
                file_url = upload_result.url

            # Send message with attachment — guard against duplicate events
            send_key = f"export_word:{event.message_id}:{contract_id}"
            if send_key not in self._processed_activity_submits:
                self._processed_activity_submits.add(send_key)
                channel = await self.client.channels.fetch(event.channel_id)
                await channel.send(
                    content=ChannelMessageContent(
                        t=f"✅ Đã xuất file Word thành công!\n\n"
                        f"📄 File: `{output_filename}`\n"
                        f"Hợp đồng: **{contract.order_id}**\n"
                        f"Chuyên gia: **{prof.pronoun} {prof.expert_name}**"
                    ),
                    attachments=[
                        ApiMessageAttachment(
                            filename=output_filename,
                            url=file_url,
                            filetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            size=os.path.getsize(output_path),
                        )
                    ],
                )

            # Edit original message to remove buttons
            await self.edit_message(
                event.channel_id,
                event.message_id,
                "✅ File đã được gửi lên channel.",
                components=[],
            )

        except Exception as e:
            self.logger.error("Error exporting Word: %s", e, exc_info=True)
            await self.edit_message(
                event.channel_id,
                event.message_id,
                f"❌ Lỗi xuất file: {e}",
                components=[],
            )

    async def _handle_acceptance_report(
        self, event: realtime_pb2.MessageButtonClicked, contract_id: int
    ) -> None:
        """Handle acceptance report button - show activity selection if multiple activities."""
        if not self.contract_service:
            await self.edit_message(
                event.channel_id,
                event.message_id,
                "❌ Contract service không khả dụng.",
                components=[],
            )
            return

        try:
            # Get contract and activities
            contract = await self.contract_service.get_contract_by_id(contract_id)
            if not contract:
                await self.edit_message(
                    event.channel_id,
                    event.message_id,
                    "❌ Không tìm thấy hợp đồng.",
                    components=[],
                )
                return

            activities = await self.contract_service.get_activities_by_contract_id(
                contract_id
            )

            if not activities:
                await self.edit_message(
                    event.channel_id,
                    event.message_id,
                    "❌ Hợp đồng chưa có hoạt động nào.",
                    components=[],
                )
                return

            # If only 1 activity, export directly
            if len(activities) == 1:
                await self._export_acceptance_direct(event, contract_id, activities)
                return

            # Multiple activities - show selection form
            await self._show_activity_selection_form(event, contract_id, activities)

        except Exception as e:
            self.logger.error("Error handling acceptance report: %s", e, exc_info=True)
            await self.edit_message(
                event.channel_id,
                event.message_id,
                f"❌ Lỗi: {e}",
                components=[],
            )

    async def _show_activity_selection_form(
        self,
        event: realtime_pb2.MessageButtonClicked,
        contract_id: int,
        activities: list[ActivityData],
    ) -> None:
        """Show activity selection form with radio buttons (multi-select)."""
        form = InteractiveBuilder("📋 Chọn hoạt động cần nghiệm thu")
        form.set_description(
            f"Hợp đồng có {len(activities)} hoạt động. Chọn 1 hoặc nhiều hoạt động để xuất biên bản:"
        )
        form.set_color("#5865F2")

        # Radio buttons for each activity (max_options allows multi-select)
        radio_options = [
            RadioFieldOption(
                label=f"{act.activity_number}: {act.activity_name}",
                value=str(act.id),
                name=str(act.id),
            )
            for act in activities
        ]
        form.add_radio_field(
            "selected_activity_ids",
            "Hoạt động",
            options=radio_options,
            max_options=len(activities),
            description="Chọn nhiều hoạt động bằng cách click vào các mục bên trên",
        )

        await self.edit_message(
            event.channel_id,
            event.message_id,
            "📋 **Chọn hoạt động cần nghiệm thu**",
            embeds=[InteractiveMessageProps(**form.build())],
            components=self._build_buttons(
                [
                    (
                        f"export_acceptance:{contract_id}",
                        "✅ Xuất biên bản",
                        ButtonMessageStyle.SUCCESS,
                    ),
                    ("cancel", "❌ Hủy", ButtonMessageStyle.DANGER),
                ]
            ),
        )

    async def _export_acceptance_direct(
        self,
        event: realtime_pb2.MessageButtonClicked,
        contract_id: int,
        activities: list[ActivityData],
    ) -> None:
        """Export acceptance report directly."""
        if not self.word_export_service or not self.contract_service:
            await self.edit_message(
                event.channel_id,
                event.message_id,
                "❌ Service không khả dụng.",
                components=[],
            )
            return

        try:
            contract = await self.contract_service.get_contract_by_id(contract_id)
            if not contract:
                await self.edit_message(
                    event.channel_id,
                    event.message_id,
                    "❌ Không tìm thấy hợp đồng.",
                    components=[],
                )
                return

            today = date_type.today()
            if contract.end_date and today > contract.end_date:
                await self.edit_message(
                    event.channel_id,
                    event.message_id,
                    "❌ Không thể nghiệm thu vì ngày nghiệm thu vượt quá ngày kết thúc hợp đồng.",
                    components=[],
                )
                return

            prof = await self.expert_service.get_expert_by_id(contract.expert_id)
            if not prof:
                await self.edit_message(
                    event.channel_id,
                    event.message_id,
                    "❌ Không tìm thấy chuyên gia.",
                    components=[],
                )
                return

            # Generate output filename
            import os

            output_dir = "exports"
            os.makedirs(output_dir, exist_ok=True)
            output_filename = (
                f"BBNT_{contract.order_id}_{prof.expert_name.replace(' ', '_')}.docx"
            )
            output_path = os.path.join(output_dir, output_filename)

            # Export acceptance report
            self.word_export_service.export_acceptance_report(
                contract, prof, activities, output_path
            )

            # Upload file
            file_url = None
            if self.s3_upload_service:
                try:
                    file_url = self.s3_upload_service.upload_file(
                        file_path=output_path,
                        object_name=output_filename,
                        content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    )
                except Exception as e:
                    self.logger.warning("S3 upload failed, trying Mezon upload: %s", e)

            if not file_url:
                upload_result = await self.client.upload_file(
                    file_path=output_path,
                    filename=output_filename,
                    content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
                file_url = upload_result.url

            # Send message with attachment — guard against duplicate events
            send_key = f"export_acceptance:{event.message_id}:{contract_id}"
            if send_key not in self._processed_activity_submits:
                self._processed_activity_submits.add(send_key)
                channel = await self.client.channels.fetch(event.channel_id)
                await channel.send(
                    content=ChannelMessageContent(
                        t=f"✅ Đã xuất biên bản nghiệm thu!\n\n"
                        f"📄 File: `{output_filename}`\n"
                        f"Hợp đồng: **{contract.order_id}**\n"
                        f"Chuyên gia: **{prof.pronoun} {prof.expert_name}**\n"
                        f"Hoạt động: {len(activities)}"
                    ),
                    attachments=[
                        ApiMessageAttachment(
                            filename=output_filename,
                            url=file_url,
                            filetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            size=os.path.getsize(output_path),
                        )
                    ],
                )

            await self.edit_message(
                event.channel_id,
                event.message_id,
                "✅ File đã được gửi lên channel.",
                components=[],
            )

        except Exception as e:
            self.logger.error("Error exporting acceptance report: %s", e, exc_info=True)
            await self.edit_message(
                event.channel_id,
                event.message_id,
                f"❌ Lỗi xuất file: {e}",
                components=[],
            )

    async def _handle_export_acceptance(
        self,
        event: realtime_pb2.MessageButtonClicked,
        contract_id: int,
        extra_data: dict[str, Any],
    ) -> None:
        """Handle export acceptance with selected activities from form."""
        if not self.contract_service:
            await self.edit_message(
                event.channel_id,
                event.message_id,
                "❌ Service không khả dụng.",
                components=[],
            )
            return

        try:
            # Get selected activity IDs from radio field (comma-separated)
            selected_ids_raw = extra_data.get("selected_activity_ids", "")
            if not selected_ids_raw:
                await self.edit_message(
                    event.channel_id,
                    event.message_id,
                    "❌ Vui lòng chọn ít nhất 1 hoạt động.",
                    components=[],
                )
                return

            # Parse selected IDs - handle both list and comma-separated string
            if isinstance(selected_ids_raw, list):
                selected_ids = [int(id_str) for id_str in selected_ids_raw]
            else:
                selected_ids = [
                    int(id_str.strip()) for id_str in selected_ids_raw.split(",")
                ]

            all_activities = await self.contract_service.get_activities_by_contract_id(
                contract_id
            )
            selected_activities = [
                act for act in all_activities if act.id in selected_ids
            ]

            if not selected_activities:
                await self.edit_message(
                    event.channel_id,
                    event.message_id,
                    "❌ Không tìm thấy hoạt động đã chọn.",
                    components=[],
                )
                return

            await self._export_acceptance_direct(
                event, contract_id, selected_activities
            )

        except Exception as e:
            self.logger.error("Error exporting acceptance: %s", e, exc_info=True)
            await self.edit_message(
                event.channel_id,
                event.message_id,
                f"❌ Lỗi xuất file: {e}",
                components=[],
            )
