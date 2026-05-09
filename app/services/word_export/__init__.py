"""Word document export service for contracts using docxtpl."""

from typing import List
from docxtpl import DocxTemplate

from app.services.contract.service import ContractData, ActivityData
from app.services.expert.service import ExpertData
from app.utils import number_to_vietnamese_text


class WordExportService:
    """Service for exporting contracts to Word documents using templates."""

    def __init__(
        self,
        template_path: str = "template/Template_HDCG.docx",
        acceptance_template_path: str = "template/Template_BBNT.docx",
    ):
        self.template_path = template_path
        self.acceptance_template_path = acceptance_template_path

    def export_contract(
        self,
        contract: ContractData,
        expert: ExpertData,
        activities: List[ActivityData],
        output_path: str,
    ) -> str:
        """Export contract to Word document using docxtpl.

        Args:
            contract: Contract data
            expert: Expert data
            activities: List of activities
            output_path: Output file path

        Returns:
            Path to generated file
        """
        # Load template
        doc = DocxTemplate(self.template_path)

        # Build context
        context = self._build_context(contract, expert, activities)

        # Render template
        doc.render(context)

        # Save document
        doc.save(output_path)
        return output_path

    def _build_context(
        self,
        contract: ContractData,
        expert: ExpertData,
        activities: List[ActivityData],
    ) -> dict:
        """Build context dictionary for template rendering."""
        issued_date_str = (
            expert.issued_date.strftime("%d/%m/%Y") if expert.issued_date else ""
        )
        end_date_str = (
            contract.end_date.strftime("%d/%m/%Y") if contract.end_date else ""
        )

        # Build activities list
        activities_list = []
        for idx, activity in enumerate(activities, start=1):
            activities_list.append(
                {
                    "stt": idx,
                    "activity_number": activity.activity_number,
                    "activity_name": activity.activity_name,
                    "budget": activity.budget or "",
                    "working_days": activity.working_days,
                    "rate": f"{activity.rate:,.0f}".replace(",", "."),
                    "real_amount": f"{activity.real_amount:,.0f}".replace(",", "."),
                    "real_amount_text": number_to_vietnamese_text(activity.real_amount),
                }
            )

        # Calculate amounts
        tax_amount = contract.total_amount * contract.tax
        final_amount_text = number_to_vietnamese_text(contract.final_amount)

        # Format additional_information with '-' prefix if not empty
        additional_info = contract.additional_information or ""
        if additional_info:
            additional_info = f"- {additional_info}"

        context = {
            # Contract info
            "order_id": contract.order_id,
            "dd": contract.dd,
            "mm": contract.mm,
            "yyyy": contract.yyyy,
            "abbreviated_project": contract.abbreviated_project or "",
            "additional_information": additional_info,
            # Expert info
            "pronoun": expert.pronoun,
            "expert_name": expert.expert_name,
            "nationality": expert.nationality or "",
            "address": expert.address or "",
            "id_number": expert.id_number or "",
            "issued_date": issued_date_str,
            "issued_place": expert.issued_place or "",
            "email_address": expert.email_address or "",
            "phone": expert.phone or "",
            "bank_account": expert.bank_account or "",
            "bank_name": expert.bank_name or "",
            # Project info (from Program)
            "sum_activities": contract.summary_activities or "",
            "activity_purpose": contract.activity_purpose or "",
            "project_name": contract.project_name or "",
            "end_date": end_date_str,
            # Activities
            "activities": activities_list,
            # Totals
            "total_amount": f"{contract.total_amount:,.0f}".replace(",", "."),
            "tax_amount": f"{tax_amount:,.0f}".replace(",", "."),
            "final_amount": f"{contract.final_amount:,.0f}".replace(",", "."),
            "text_amount": final_amount_text,
        }

        return context

    def export_acceptance_report(
        self,
        contract: ContractData,
        expert: ExpertData,
        activities: List[ActivityData],
        output_path: str,
    ) -> str:
        """Export acceptance report (biên bản nghiệm thu) to Word document.

        Args:
            contract: Contract data
            expert: Expert data
            activities: List of activities to include in acceptance report
            output_path: Output file path

        Returns:
            Path to generated file
        """
        # Load acceptance template
        doc = DocxTemplate(self.acceptance_template_path)

        # Build context for acceptance report
        context = self._build_acceptance_context(contract, expert, activities)

        # Render template
        doc.render(context)

        # Save document
        doc.save(output_path)
        return output_path

    def _build_acceptance_context(
        self,
        contract: ContractData,
        expert: ExpertData,
        activities: List[ActivityData],
    ) -> dict:
        """Build context dictionary for acceptance report template rendering."""
        issued_date_str = (
            expert.issued_date.strftime("%d/%m/%Y") if expert.issued_date else ""
        )
        end_date_str = (
            contract.end_date.strftime("%d/%m/%Y") if contract.end_date else ""
        )

        # Build activities list
        activities_list = []
        total_accepted_amount = 0.0
        for idx, activity in enumerate(activities, start=1):
            activities_list.append(
                {
                    "stt": idx,
                    "activity_number": activity.activity_number,
                    "activity_name": activity.activity_name,
                    "budget": activity.budget or "",
                    "working_days": activity.working_days,
                    "rate": f"{activity.rate:,.0f}".replace(",", "."),
                    "real_amount": f"{activity.real_amount:,.0f}".replace(",", "."),
                    "real_amount_text": number_to_vietnamese_text(activity.real_amount),
                }
            )
            total_accepted_amount += activity.real_amount

        # Calculate tax and final amount for accepted activities
        tax_amount = total_accepted_amount * contract.tax
        final_accepted_amount = total_accepted_amount - tax_amount
        final_accepted_amount_text = number_to_vietnamese_text(final_accepted_amount)

        # Format additional_information with '-' prefix if not empty
        additional_info = contract.additional_information or ""
        if additional_info:
            additional_info = f"- {additional_info}"

        context = {
            # Contract info
            "order_id": contract.order_id,
            "dd": contract.dd,
            "mm": contract.mm,
            "yyyy": contract.yyyy,
            "abbreviated_project": contract.abbreviated_project or "",
            "additional_information": additional_info,
            # Expert info
            "pronoun": expert.pronoun,
            "expert_name": expert.expert_name,
            "nationality": expert.nationality or "",
            "address": expert.address or "",
            "id_number": expert.id_number or "",
            "issued_date": issued_date_str,
            "issued_place": expert.issued_place or "",
            "email_address": expert.email_address or "",
            "phone": expert.phone or "",
            "bank_account": expert.bank_account or "",
            "bank_name": expert.bank_name or "",
            # Project info
            "sum_activities": contract.summary_activities or "",
            "activity_purpose": contract.activity_purpose or "",
            "project_name": contract.project_name or "",
            "end_date": end_date_str,
            # Activities (only selected ones for acceptance)
            "activities": activities_list,
            # Totals (for accepted activities only)
            "total_amount": f"{total_accepted_amount:,.0f}".replace(",", "."),
            "tax_amount": f"{tax_amount:,.0f}".replace(",", "."),
            "final_amount": f"{final_accepted_amount:,.0f}".replace(",", "."),
            "text_amount": final_accepted_amount_text,
        }

        return context
