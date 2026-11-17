"""LLM client interface.

Implementations: OpenAI-compatible API (dev) and self-hosted open model (production).
Temperature is always 0 for extraction tasks to maximize determinism.

Prompt-injection defense: document text is always passed as data, never as instructions.
All inputs are treated as untrusted data.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class LLMMessage:
    """A single message in a chat completion."""

    def __init__(self, role: str, content: str) -> None:
        self.role = role
        self.content = content

    def to_dict(self) -> dict[str, str]:
        return {"role": self.role, "content": self.content}


class LLMResponse:
    """Response from an LLM call."""

    def __init__(
        self,
        content: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        raw: Any = None,
    ) -> None:
        self.content = content
        self.model = model
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens
        self.raw = raw


class LLMClient(ABC):
    """Abstract LLM client interface.

    All implementations must:
    - Return structured JSON when json_schema is provided
    - Retry on invalid JSON up to max_retries times
    - Never raise on soft errors; return an error-flagged response
    - Support temperature=0 for deterministic extraction
    """

    @abstractmethod
    async def complete(
        self,
        messages: list[LLMMessage],
        json_schema: dict[str, Any] | None = None,
        temperature: float = 0.0,
        max_tokens: int = 4096,
        max_retries: int = 3,
    ) -> LLMResponse:
        """Send a chat completion request and return the response."""
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the backend is reachable."""
        ...


class StubLLMClient(LLMClient):
    """Stub LLM client for testing. Returns configurable fixed responses."""

    def __init__(self, fixed_response: str = '{"result": "stub"}') -> None:
        self._fixed_response = fixed_response

    async def complete(
        self,
        messages: list[LLMMessage],
        json_schema: dict[str, Any] | None = None,
        temperature: float = 0.0,
        max_tokens: int = 4096,
        max_retries: int = 3,
    ) -> LLMResponse:
        return LLMResponse(
            content=self._fixed_response,
            model="stub",
            prompt_tokens=0,
            completion_tokens=0,
        )

    def is_available(self) -> bool:
        return True
