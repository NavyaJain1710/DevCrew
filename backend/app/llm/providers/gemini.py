"""
Google Gemini LLM provider — uses Google's OpenAI-compatible REST API.

Free tier (as of 2025):
  - gemini-1.5-flash  : 1 500 req/day, 1 000 000 tokens/min  ← best free fast model
  - gemini-1.5-pro    : 50 req/day, 32 000 tokens/min         ← best free smart model
  - gemini-2.0-flash  : 1 500 req/day                         ← newest fast model

Get your free API key at: https://aistudio.google.com/app/apikey
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

# Approximate cost table (USD per 1K tokens).
# Free-tier keys have $0 cost but rate limits apply.
_GEMINI_COST_TABLE: dict[str, tuple[float, float]] = {
    "gemini-1.5-flash":         (0.000075, 0.0003),
    "gemini-1.5-flash-8b":      (0.0000375, 0.00015),
    "gemini-1.5-pro":           (0.00125, 0.005),
    "gemini-2.0-flash":         (0.000075, 0.0003),
    "gemini-2.0-flash-lite":    (0.000075, 0.0003),
}

_DEFAULT_COST = (0.0001, 0.0003)

# Google's OpenAI-compatible base URL
_GEMINI_OPENAI_BASE = "https://generativelanguage.googleapis.com/v1beta/openai"


class GeminiProvider(LLMProvider):
    """
    Google Gemini provider using the OpenAI-compatible REST endpoint.
    No extra SDK required — uses the same httpx client pattern as other providers.
    """

    provider_name = "gemini"

    def __init__(self, model: str = "gemini-1.5-flash") -> None:
        self.model = model
        base_url = settings.gemini_base_url or _GEMINI_OPENAI_BASE
        self._client = httpx.AsyncClient(
            base_url=base_url,
            headers={
                "Authorization": f"Bearer {settings.gemini_api_key}",
                "Content-Type": "application/json",
            },
            timeout=120.0,  # Gemini can be slightly slower on Pro
            verify=False,
        )

    # ── generate ──────────────────────────────────────────────────────────────

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
        prompt_tokens = usage.get("prompt_tokens", 0) or max(1, len(prompt) // 4)
        completion_tokens = usage.get("completion_tokens", 0) or max(1, len(choice["message"]["content"]) // 4)

        return LLMResponse(
            content=choice["message"]["content"],
            model=self.model,
            provider=self.provider_name,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            latency_ms=timer.elapsed_ms,
            raw_response=data,
        )

    # ── generate_structured ───────────────────────────────────────────────────

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
            f"Respond ONLY with a valid JSON object matching this schema:\n"
            f"```json\n{schema_json}\n```"
        )
        resp = await self.generate(prompt, system=structured_system, temperature=temperature)
        parsed = self._parse_json(resp.content, schema)
        return parsed, resp

    # ── stream ────────────────────────────────────────────────────────────────

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

    # ── helpers ───────────────────────────────────────────────────────────────

    def count_tokens(self, text: str) -> int:
        # Gemini uses ~4 chars per token (same heuristic as other providers)
        return len(text) // 4

    def _parse_json(self, content: str, schema: Type[BaseModel]) -> BaseModel:
        content = content.strip()
        for attempt in [
            content,
            re.search(r"```(?:json)?\s*([\s\S]*?)```", content),
            re.search(r"\{[\s\S]*\}", content),
        ]:
            try:
                text = attempt.group(1).strip() if hasattr(attempt, "group") else (attempt or "")
                return schema.model_validate_json(text)
            except Exception:
                continue
        raise ValueError(f"Could not parse JSON from Gemini response: {content[:300]}")
