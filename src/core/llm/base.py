"""Base interfaces for LLM clients."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Iterable, Optional


class LLMClient(ABC):
    """Abstract interface for Large Language Model clients."""

    @abstractmethod
    def generate(self, prompt: str, **kwargs: Any) -> str:
        """Generate a completion from a prompt."""
        raise NotImplementedError

    def generate_batch(self, prompts: Iterable[str], **kwargs: Any) -> Iterable[str]:
        """Optional batch generation; default iterates generate."""
        for prompt in prompts:
            yield self.generate(prompt, **kwargs)

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Return the underlying model name."""
        raise NotImplementedError


class ChatMessage(Dict[str, str]):
    """Typed alias for chat messages (role/content)."""

    role: str
    content: str


__all__ = ["LLMClient", "ChatMessage"]
