"""Form state tracking for interactive message submissions."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any


@dataclass
class PendingForm:
    """Tracks an interactive form sent to a user."""

    action: str  # "add", "edit", "delete_confirm", "select_prof"
    professional_id: int | None = None
    channel_id: int = 0
    user_id: int = 0


class FormStateTracker:
    """Thread-safe tracker for pending interactive forms."""

    def __init__(self) -> None:
        self._forms: dict[str, PendingForm] = {}  # composite key -> PendingForm

    def register(self, action: str, prof_id: int | None = None) -> str:
        key = f"{action}:{prof_id}" if prof_id else action
        self._forms[key] = PendingForm(action=action, professional_id=prof_id)
        return key

    def lookup(self, key: str) -> PendingForm | None:
        return self._forms.get(key)

    def complete(self, key: str) -> PendingForm | None:
        return self._forms.pop(key, None)

    @staticmethod
    def parse_extra_data(extra_data: str) -> dict[str, Any]:
        """Parse extra_data JSON string from button click event."""
        try:
            return json.loads(extra_data) if extra_data else {}
        except (json.JSONDecodeError, TypeError):
            return {}


form_tracker = FormStateTracker()
