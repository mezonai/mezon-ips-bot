"""Utility functions for formatting."""

from datetime import date as date_type


def format_currency_vn(amount: float) -> str:
    """Format currency in Vietnamese style (500.000 VNĐ)."""
    return f"{amount:,.0f}".replace(",", ".") + " VNĐ"


def format_date_vn(date: date_type) -> str:
    """Format date as dd/mm/yyyy with zero padding."""
    return date.strftime("%d/%m/%Y")
