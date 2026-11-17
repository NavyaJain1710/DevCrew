"""
OpenRouter LLM provider.
Uses the OpenAI-compatible API surface exposed by OpenRouter.
Supports structured outputs via JSON mode + Pydantic schema injection.
"""

from __future__ import annotations

import json
import re
from typing import AsyncIterator, Type

import httpx
from pydantic import BaseModel

from app.config import get_settings
from app.llm.base import LLMProvider, LLMResponse, LLMStreamChunk

settings = get_settings()

# Per-model token cost in USD per 1K tokens (prompt / completion)
# Updated for major models — adjust as providers change pricing
_COST_TABLE: dict[str, tuple[float, float]] = {
    "anthropic/claude-3-5-sonnet": (0.003, 0.015),
    "anthropic/claude-3-5-haiku": (0.0008, 0.004),
    "openai/gpt-4o": (0.005, 0.015),
    "openai/gpt-4o-mini": (0.00015, 0.0006),
    "qwen/qwen2.5-coder-32b-instruct": (0.0007, 0.0014),
    "meta-llama/llama-3.1-8b-instruct": (0.00005, 0.0001),
    "meta-llama/llama-3.3-70b-instruct": (0.00059, 0.00079),
    "google/gemini-1.5-pro": (0.00125, 0.005),
    "mistralai/mixtral-8x7b-instruct": (0.00045, 0.00070),
}

_DEFAULT_COST = (0.001, 0.002)


class OpenRouterProvider(LLMProvider):
    """OpenRouter provider — wraps the OpenAI-compatible REST API."""

    provider_name = "openrouter"

    def __init__(self, model: str) -> None:
        self.model = model
        self._client = httpx.AsyncClient(
            base_url=settings.openrouter_base_url,
            headers={
                "Authorization": f"Bearer {settings.openrouter_api_key}",
                "HTTP-Referer": "https://devcrew.ai",
                "X-Title": "DevCrew",
                "Content-Type": "application/json",
            },
            timeout=120.0,
            verify=False,
        )

    async def generate(
        self,
        prompt: str,
        system: str = "",
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        with self._timer() as timer:
            resp = await self._client.post(
                "/chat/completions",
                json={
                    "model": self.model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
            )
            resp.raise_for_status()
            data = resp.json()

        choice = data["choices"][0]
        usage = data.get("usage", {})
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        cost = self._estimate_cost(prompt_tokens, completion_tokens)

        return LLMResponse(
            content=choice["message"]["content"],
            model=self.model,
            provider=self.provider_name,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            latency_ms=timer.elapsed_ms,
            raw_response=data,
        )

    async def generate_structured(
        self,
        prompt: str,
        schema: Type[BaseModel],
        system: str = "",
        temperature: float = 0.1,
    ) -> tuple[BaseModel, LLMResponse]:
        schema_json = json.dumps(schema.model_json_schema(), indent=2)
        structured_system = (
            f"{system}\n\n"
            f"You MUST respond with a valid JSON object conforming EXACTLY to this schema:\n"
            f"```json\n{schema_json}\n```\n"
            f"Return ONLY the JSON object. No markdown. No explanation."
        )
        resp = await self.generate(
            prompt=prompt,
            system=structured_system,
            temperature=temperature,
            max_tokens=8192,
        )
        parsed = self._parse_json_response(resp.content, schema)
        return parsed, resp

    async def stream(
        self,
        prompt: str,
        system: str = "",
        temperature: float = 0.3,
    ) -> AsyncIterator[LLMStreamChunk]:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        async with self._client.stream(
            "POST",
            "/chat/completions",
            json={
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "stream": True,
            },
        ) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if not line.startswith("data: "):
                    continue
                data_str = line[6:]
                if data_str == "[DONE]":
                    yield LLMStreamChunk(delta="", is_final=True)
                    return
                try:
                    data = json.loads(data_str)
                    delta = data["choices"][0].get("delta", {}).get("content", "")
                    if delta:
                        yield LLMStreamChunk(delta=delta)
                except (json.JSONDecodeError, KeyError):
                    continue

    def count_tokens(self, text: str) -> int:
        # Rough approximation: 4 chars ≈ 1 token
        return len(text) // 4

    def _estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        prompt_cost_per_k, completion_cost_per_k = _COST_TABLE.get(
            self.model, _DEFAULT_COST
        )
        return (prompt_tokens / 1000 * prompt_cost_per_k) + (
            completion_tokens / 1000 * completion_cost_per_k
        )

    def _parse_json_response(self, content: str, schema: Type[BaseModel]) -> BaseModel:
        """Extract JSON from LLM response and parse into Pydantic model."""
        # Try direct parse
        content = content.strip()
        try:
            return schema.model_validate_json(content)
        except Exception:
            pass
        # Try extracting JSON from markdown code block
        match = re.search(r"```(?:json)?\s*([\s\S]*?)```", content)
        if match:
            try:
                return schema.model_validate_json(match.group(1).strip())
            except Exception:
                pass
        # Try finding first { ... } block
        match = re.search(r"\{[\s\S]*\}", content)
        if match:
            try:
                return schema.model_validate_json(match.group(0))
            except Exception:
                pass
        raise ValueError(
            f"Could not parse structured response.\nContent:\n{content[:500]}"
        )
