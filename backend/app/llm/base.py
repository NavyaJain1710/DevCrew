"""
LLM Provider abstract base class.
All concrete providers must implement this interface.
Agent code only depends on LLMProvider — never on specific SDK classes.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Optional, Type

from pydantic import BaseModel


@dataclass
class LLMResponse:
    """Structured response from any LLM provider."""

    content: str
    model: str
    provider: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    latency_ms: int = 0
    raw_response: Any = field(default=None, repr=False)


@dataclass
class LLMStreamChunk:
    """A single chunk from a streaming response."""

    delta: str
    is_final: bool = False


class LLMProvider(ABC):
    """Abstract base class for all LLM providers."""

    provider_name: str = "base"

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system: str = "",
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        """Generate a completion. Returns structured LLMResponse."""
        ...

    @abstractmethod
    async def generate_structured(
        self,
        prompt: str,
        schema: Type[BaseModel],
        system: str = "",
        temperature: float = 0.1,
        max_tokens: int = 8192,
    ) -> tuple[BaseModel, LLMResponse]:
        """
        Generate a structured output conforming to a Pydantic schema.
        Returns (parsed_model, raw_llm_response).
        """
        ...

    @abstractmethod
    async def stream(
        self,
        prompt: str,
        system: str = "",
        temperature: float = 0.3,
    ) -> AsyncIterator[LLMStreamChunk]:
        """Stream a completion token by token."""
        ...

    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """Estimate token count for a given text string."""
        ...

    def _timer(self) -> "_Timer":
        return _Timer()


class _Timer:
    """Context manager to measure latency in milliseconds."""

    def __enter__(self) -> "_Timer":
        self._start = time.perf_counter()
        return self

    def __exit__(self, *_: Any) -> None:
        self._end = time.perf_counter()

    @property
    def elapsed_ms(self) -> int:
        return int((self._end - self._start) * 1000)
