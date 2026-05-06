"""Professional (expert) management handler with interactive forms."""

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
    SelectFieldOption,
    RadioFieldOption,
)
from mezon.protobuf.rtapi import realtime_pb2

from .base import BaseMessageHandler, command
from app.services.bot.form_tracker import form_tracker
from app.services.professional.service import ProfessionalService, ProfessionalData


PRONOUNS = ["Ông", "Bà", "Cô", "Anh", "Chị", "Ms.", "Mr."]
NATIONALITIES = [
    SelectFieldOption(label="Việt Nam", value="Việt Nam"),
    SelectFieldOption(label="Mỹ", value="Mỹ"),
    SelectFieldOption(label="Hàn Quốc", value="Hàn Quốc"),
    SelectFieldOption(label="Nhật Bản", value="Nhật Bản"),
    SelectFieldOption(label="Trung Quốc", value="Trung Quốc"),
    SelectFieldOption(label="Khác", value="Khác"),
]


class ProfessionalHandler(BaseMessageHandler):
    """Handler for *professional command to manage experts."""

    def __init__(self, client, professional_service: ProfessionalService):
        super().__init__(client)
        self.professional_service = professional_service

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

    def _build_add_form(self) -> InteractiveBuilder:
        """Build the interactive form for adding a new professional."""
        form = InteractiveBuilder("➕ Thêm chuyên gia mới")
        form.set_description("Điền thông tin chuyên gia bên dưới")
        form.set_color("#5865F2")

        form.add_select_field(
            "pronoun",
            "Xưng hô",
            options=[SelectFieldOption(label=p, value=p) for p in PRONOUNS],
            description="Chọn xưng hô",
        )
        form.add_input_field(
            "expert_name",
            "Họ và tên",
            placeholder="Nguyễn Văn A",
            description="Họ tên đầy đủ của chuyên gia",
        )
        form.add_select_field(
            "nationality",
            "Quốc tịch",
            options=NATIONALITIES,
            description="Quốc tịch",
        )
        form.add_input_field(
            "address",
            "Địa chỉ",
            placeholder="Số nhà, đường, phường/xã, quận/huyện, tỉnh/thành phố",
            description="Địa chỉ liên hệ",
            options=InputFieldOption(textarea=True),
        )
        form.add_input_field(
            "id_number",
            "Số CCCD",
            placeholder="012345678901",
            description="Số căn cước công dân",
        )
        form.add_datepicker_field(
            "issued_date",
            "Ngày cấp",
            description="Ngày cấp CCCD",
        )
        form.add_input_field(
            "issued_place",
            "Nơi cấp",
            placeholder="Cục CSQLHC về TTXH",
            description="Nơi cấp CCCD",
        )
        form.add_input_field(
            "email_address",
            "Email",
            placeholder="email@example.com",
            description="Địa chỉ email",
            options=InputFieldOption(type="email"),
        )
        form.add_input_field(
            "phone",
            "Số điện thoại",
            placeholder="0912345678",
            description="Số điện thoại liên hệ",
        )
        form.add_input_field(
            "bank_account",
            "Số tài khoản",
            placeholder="1234567890",
            description="Số tài khoản ngân hàng",
        )
        form.add_input_field(
            "bank_name",
            "Ngân hàng",
            placeholder="Vietcombank",
            description="Tên ngân hàng",
        )
        form.add_input_field(
            "rate",
            "Rate",
            placeholder="500000",
            description="Mức lương/giá thuê (VNĐ)",
            options=InputFieldOption(type="number"),
        )
        return form

    def _build_edit_form(self, p: ProfessionalData) -> InteractiveBuilder:
        """Build the interactive form for editing a professional."""
        form = InteractiveBuilder(f"✏️ Sửa thông tin: {p.pronoun} {p.expert_name}")
        form.set_description("Chỉnh sửa thông tin chuyên gia")
        form.set_color("#F59E0B")

        form.add_select_field(
            "pronoun",
            "Xưng hô",
            options=[SelectFieldOption(label=pr, value=pr) for pr in PRONOUNS],
            description="Chọn xưng hô",
        )
        form.add_input_field(
            "expert_name",
            "Họ và tên",
            placeholder="Nguyễn Văn A",
            description="Họ tên đầy đủ của chuyên gia",
            options=InputFieldOption(defaultValue=p.expert_name),
        )
        form.add_select_field(
            "nationality",
            "Quốc tịch",
            options=NATIONALITIES,
            description="Quốc tịch",
        )
        form.add_input_field(
            "address",
            "Địa chỉ",
            placeholder="Địa chỉ liên hệ",
            description="Địa chỉ liên hệ",
            options=InputFieldOption(textarea=True, defaultValue=p.address or ""),
        )
        form.add_input_field(
            "id_number",
            "Số CCCD",
            placeholder="012345678901",
            description="Số căn cước công dân",
            options=InputFieldOption(defaultValue=p.id_number or ""),
        )
        form.add_datepicker_field(
            "issued_date",
            "Ngày cấp",
            description="Ngày cấp CCCD",
        )
        form.add_input_field(
            "issued_place",
            "Nơi cấp",
            placeholder="Nơi cấp CCCD",
            description="Nơi cấp CCCD",
            options=InputFieldOption(defaultValue=p.issued_place or ""),
        )
        form.add_input_field(
            "email_address",
            "Email",
            placeholder="email@example.com",
            description="Địa chỉ email",
            options=InputFieldOption(type="email", defaultValue=p.email_address or ""),
        )
        form.add_input_field(
            "phone",
            "Số điện thoại",
            placeholder="0912345678",
            description="Số điện thoại liên hệ",
            options=InputFieldOption(defaultValue=p.phone or ""),
        )
        form.add_input_field(
            "bank_account",
            "Số tài khoản",
            placeholder="1234567890",
            description="Số tài khoản ngân hàng",
            options=InputFieldOption(defaultValue=p.bank_account or ""),
        )
        form.add_input_field(
            "bank_name",
            "Ngân hàng",
            placeholder="Vietcombank",
            description="Tên ngân hàng",
            options=InputFieldOption(defaultValue=p.bank_name or ""),
        )
        form.add_input_field(
            "rate",
            "Rate",
            placeholder="500000",
            description="Mức lương/giá thuê (VNĐ)",
            options=InputFieldOption(type="number", defaultValue=str(p.rate or "")),
        )
        return form

    def _format_professional(self, p: ProfessionalData) -> str:
        """Format a single professional record."""
        lines = [
            f"👤 **{p.pronoun} {p.expert_name}** (ID: {p.id})",
            f"   Quốc tịch: {p.nationality or '—'}",
            f"   Địa chỉ: {p.address or '—'}",
            f"   CCCD: {p.id_number or '—'}",
            f"   Ngày cấp: {p.issued_date.strftime('%d/%m/%Y') if p.issued_date else '—'}",
            f"   Nơi cấp: {p.issued_place or '—'}",
            f"   Email: {p.email_address or '—'}",
            f"   SĐT: {p.phone or '—'}",
            f"   Ngân hàng: {p.bank_name or '—'} / {p.bank_account or '—'}",
            f"   Rate: {p.rate:,.0f} VNĐ" if p.rate else "   Rate: —",
        ]
        return "\n".join(lines)

    @command("*professional")
    async def handle_professional(
        self,
        message: Any,
        subcmd: str = None,
        rest: str = None,
    ) -> None:
        """Manage professionals (experts).

        Usage:
            *professional
            *professional list
            *professional add
            *professional edit <id>
            *professional delete <id>
            *professional find name <search_term>
            *professional find id <cccd_number>
        """
        if not subcmd:
            form = InteractiveBuilder("📋 Quản lý chuyên gia")
            form.set_description("Chọn thao tác bên dưới")
            form.set_color("#5865F2")

            form.add_radio_field(
                "action",
                "Thao tác",
                options=[
                    RadioFieldOption(
                        label="📝 Thêm chuyên gia mới",
                        value="add",
                        description="Tạo chuyên gia mới",
                    ),
                    RadioFieldOption(
                        label="📄 Danh sách chuyên gia",
                        value="list",
                        description="Xem tất cả chuyên gia",
                    ),
                    RadioFieldOption(
                        label="✏️ Sửa thông tin",
                        value="edit",
                        description="Chỉnh sửa chuyên gia",
                    ),
                    RadioFieldOption(
                        label="🗑️ Xóa chuyên gia",
                        value="delete",
                        description="Xóa chuyên gia",
                    ),
                    RadioFieldOption(
                        label="🔍 Tìm kiếm",
                        value="find",
                        description="Tìm chuyên gia theo tên hoặc CCCD",
                    ),
                ],
                description="Chọn thao tác bạn muốn thực hiện",
            )

            await self.reply_message(
                message,
                "📋 **Quản lý chuyên gia**\n\n"
                "Chọn thao tác ở trên, hoặc dùng trực tiếp:\n"
                "`*professional list` - Danh sách\n"
                "`*professional add` - Thêm mới\n"
                "`*professional edit <id>` - Sửa\n"
                "`*professional delete <id>` - Xóa\n"
                "`*professional find name <tên>` - Tìm theo tên\n"
                "`*professional find id <cccd>` - Tìm theo CCCD",
                embeds=[InteractiveMessageProps(**form.build())],
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
                "Dùng `*professional` để xem danh sách lệnh.",
            )

    async def _handle_list(self, message: Any) -> None:
        professionals = await self.professional_service.list_all()
        if not professionals:
            await self.reply_message(
                message, "📋 Chưa có chuyên gia nào trong hệ thống."
            )
            return

        form = InteractiveBuilder("📋 Danh sách chuyên gia")
        form.set_color("#10B981")
        form.set_description(f"Tổng cộng: {len(professionals)} chuyên gia")

        for p in professionals:
            form.add_field(
                f"{p.id}. {p.pronoun} {p.expert_name}",
                f"CCCD: {p.id_number or '—'} | SĐT: {p.phone or '—'} | Rate: {p.rate:,.0f} VNĐ"
                if p.rate
                else f"CCCD: {p.id_number or '—'} | SĐT: {p.phone or '—'}",
            )

        await self.reply_message(
            message,
            f"📋 **Danh sách {len(professionals)} chuyên gia:**",
            embeds=[InteractiveMessageProps(**form.build())],
        )

    async def _handle_add(self, message: Any) -> None:
        """Send interactive form to add a new professional."""
        form = self._build_add_form()
        buttons = self._build_form_buttons()

        await self.reply_message(
            message,
            "📝 Vui lòng điền thông tin chuyên gia bên dưới:",
            embeds=[InteractiveMessageProps(**form.build())],
            components=buttons,
        )

    async def _handle_edit(self, message: Any, rest: str | None) -> None:
        """Send interactive form to edit a professional."""
        if not rest:
            # Show list first
            professionals = await self.professional_service.list_all()
            if not professionals:
                await self.reply_message(message, "📋 Chưa có chuyên gia nào để sửa.")
                return

            form = InteractiveBuilder("✏️ Chọn chuyên gia cần sửa")
            form.set_description("Chọn ID chuyên gia muốn chỉnh sửa")
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
                    for p in professionals[:10]
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

        try:
            prof_id = int(rest.strip())
        except ValueError:
            await self.reply_message(message, "❌ ID phải là số.")
            return

        existing = await self.professional_service.get_professional_by_id(prof_id)
        if not existing:
            await self.reply_message(
                message, f"❌ Không tìm thấy chuyên gia với ID: {prof_id}"
            )
            return

        form = self._build_edit_form(existing)

        await self.reply_message(
            message,
            f"✏️ Đang sửa thông tin chuyên gia: **{existing.pronoun} {existing.expert_name}**",
            embeds=[InteractiveMessageProps(**form.build())],
            components=self._build_edit_buttons(prof_id),
        )

    async def _handle_delete(self, message: Any, rest: str | None) -> None:
        """Send confirmation to delete a professional."""
        if not rest:
            await self.reply_message(
                message, "❌ Thiếu ID.\nCách dùng: `*professional delete <id>`"
            )
            return

        try:
            prof_id = int(rest.strip())
        except ValueError:
            await self.reply_message(message, "❌ ID phải là số.")
            return

        existing = await self.professional_service.get_professional_by_id(prof_id)
        if not existing:
            await self.reply_message(
                message, f"❌ Không tìm thấy chuyên gia với ID: {prof_id}"
            )
            return

        form = InteractiveBuilder("⚠️ Xác nhận xóa")
        form.set_description(
            f"Bạn có chắc chắn muốn xóa chuyên gia:\n"
            f"**{existing.pronoun} {existing.expert_name}** (ID: {prof_id})\n"
            f"CCCD: {existing.id_number or '—'}"
        )
        form.set_color("#EF4444")

        await self.reply_message(
            message,
            f"⚠️ Xác nhận xóa chuyên gia: **{existing.pronoun} {existing.expert_name}**",
            embeds=[InteractiveMessageProps(**form.build())],
            components=self._build_delete_buttons(prof_id),
        )

    async def _handle_find(self, message: Any, rest: str | None) -> None:
        if not rest:
            await self.reply_message(
                message,
                "❌ Thiếu thông tin tìm kiếm.\n"
                "Cách dùng:\n"
                "  `*professional find name <tên>` - Tìm theo tên\n"
                "  `*professional find id <cccd>` - Tìm theo CCCD",
            )
            return

        parts = rest.strip().split(maxsplit=1)
        if len(parts) < 2 or not parts[1].strip():
            await self.reply_message(message, "❌ Thiếu từ khóa tìm kiếm.")
            return

        search_type = parts[0].lower()
        keyword = parts[1].strip()

        if search_type == "name":
            results = await self.professional_service.find_by_name(keyword)
            if not results:
                await self.reply_message(
                    message,
                    f"❌ Không tìm thấy chuyên gia nào với tên chứa: `{keyword}`",
                )
                return

            form = InteractiveBuilder(f"🔍 Kết quả tìm kiếm: `{keyword}`")
            form.set_color("#3B82F6")
            form.set_description(f"Tìm thấy {len(results)} chuyên gia")

            for p in results:
                form.add_field(
                    f"{p.pronoun} {p.expert_name}",
                    f"ID: {p.id} | CCCD: {p.id_number or '—'} | SĐT: {p.phone or '—'}",
                )

            await self.reply_message(
                message,
                f"🔍 Tìm thấy {len(results)} chuyên gia:",
                embeds=[InteractiveMessageProps(**form.build())],
            )

        elif search_type == "id":
            result = await self.professional_service.find_by_id_number(keyword)
            if not result:
                await self.reply_message(
                    message, f"❌ Không tìm thấy chuyên gia với CCCD: `{keyword}`"
                )
                return

            form = InteractiveBuilder("🔍 Kết quả tìm kiếm")
            form.set_color("#3B82F6")
            form.set_description(self._format_professional(result))

            await self.reply_message(
                message,
                "🔍 Kết quả tìm kiếm:",
                embeds=[InteractiveMessageProps(**form.build())],
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

            await self.edit_message(
                event.channel_id,
                event.message_id,
                "❌ Không xử lý được nút này.",
                components=[],
            )

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
        success = await self.professional_service.delete_professional(prof_id)
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

            rate = None
            if extra_data.get("rate"):
                try:
                    rate = float(
                        extra_data["rate"].strip().replace(".", "").replace(",", "")
                    )
                except (ValueError, TypeError):
                    pass

            data = ProfessionalData(
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
                rate=rate,
            )

            created = await self.professional_service.create_professional(data)
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
            self.logger.error("Error saving professional: %s", e)
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
        existing = await self.professional_service.get_professional_by_id(prof_id)
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

        rate = existing.rate
        if extra_data.get("rate"):
            try:
                rate = float(
                    extra_data["rate"].strip().replace(".", "").replace(",", "")
                )
            except (ValueError, TypeError):
                pass

        data = ProfessionalData(
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
            rate=rate,
        )

        updated = await self.professional_service.update_professional(prof_id, data)
        if updated:
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
        """Handle professional selection from list."""
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

        existing = await self.professional_service.get_professional_by_id(prof_id)
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
