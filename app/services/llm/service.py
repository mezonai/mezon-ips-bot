class LLMService:
    """Service for LLM operations."""

    def __init__(self): ...

    async def generate_response(self, prompt: str) -> str:
        """Generate a response from the LLM."""
        return prompt + " random response from LLM"
