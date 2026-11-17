"""
Groq LLM provider — ultra-fast inference via Groq's OpenAI-compatible API.
Used primarily for the fast/cheap model tier.
"""

from __future__ import annotations

import asyncio
import json
import re
from typing import AsyncIterator, Type

import httpx
import structlog
from pydantic import BaseModel

from app.config import get_settings
from app.llm.base import LLMProvider, LLMResponse, LLMStreamChunk

logger = structlog.get_logger(__name__)
settings = get_settings()

_GROQ_COST_TABLE: dict[str, tuple[float, float]] = {
    "openai/gpt-oss-20b": (0.0001, 0.00015),
    "openai/gpt-oss-120b": (0.0005, 0.00075),
    "meta-llama/llama-3.1-8b-instruct": (0.00005, 0.00008),
    "meta-llama/llama-3.3-70b-versatile": (0.00059, 0.00079),
    "llama-3.1-8b-instant": (0.00005, 0.00008),
    "llama-3.3-70b-versatile": (0.00059, 0.00079),
    "mixtral-8x7b-32768": (0.00024, 0.00024),
    "qwen/qwen3.8-27b": (0.00029, 0.00039),
    "qwen-qwen2.5-coder-32b": (0.00029, 0.00039),
}

_DEFAULT_COST = (0.0001, 0.0002)

MAX_RETRIES = 5
RETRY_BASE_DELAY = 5  # seconds


class GroqProvider(LLMProvider):
    """Groq provider — wraps Groq's OpenAI-compatible REST API."""

    provider_name = "groq"

    def __init__(self, model: str) -> None:
        import os
        self.model = model
        api_key = settings.groq_api_key or os.getenv("GROQ_API_KEY", "")
        self._client = httpx.AsyncClient(
            base_url=settings.groq_base_url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            timeout=120.0,
            verify=False,
        )

    async def _post_with_retry(self, payload: dict) -> dict:
        """POST to /chat/completions with exponential backoff on 429 or network errors."""
        last_resp = None
        for attempt in range(MAX_RETRIES):
            try:
                last_resp = await self._client.post("/chat/completions", json=payload)
            except (httpx.RequestError, Exception) as net_err:
                wait = RETRY_BASE_DELAY * (2 ** attempt)
                logger.warning(
                    "groq_network_error",
                    attempt=attempt + 1,
                    max_attempts=MAX_RETRIES,
                    wait_seconds=wait,
                    error=str(net_err),
                    model=self.model,
                )
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(wait)
                    continue
                raise

            if last_resp.status_code == 429:
                retry_after_header = last_resp.headers.get("retry-after", "")
                try:
                    retry_after = int(retry_after_header)
                except (ValueError, TypeError):
                    retry_after = 0
                wait = max(retry_after, RETRY_BASE_DELAY * (2 ** attempt))

                # Auto-tune max_tokens if OTPM (output tokens per minute) limit hit
                if "output tokens per minute" in last_resp.text.lower():
                    payload["max_tokens"] = min(payload.get("max_tokens", 2048), 1024)

                logger.warning(
                    "groq_rate_limited",
                    attempt=attempt + 1,
                    max_attempts=MAX_RETRIES,
                    wait_seconds=wait,
                    model=self.model,
                )
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(wait)
                    continue

            if last_resp.status_code != 200:
                logger.error("groq_api_error", status=last_resp.status_code, body=last_resp.text[:300])
            last_resp.raise_for_status()
            return last_resp.json()

        if last_resp is not None:
            last_resp.raise_for_status()
        raise RuntimeError("Max retries exceeded")

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

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        
        with self._timer() as timer:
            data = await self._post_with_retry(payload)

        choice = data["choices"][0]
        content = choice["message"]["content"]
        
        usage = data.get("usage", {})
        prompt_tokens = usage.get("prompt_tokens", 0) or max(1, len(prompt) // 4)
        completion_tokens = usage.get("completion_tokens", 0) or max(1, len(content) // 4)

        return LLMResponse(
            content=content,
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
        max_tokens: int = 8192,
    ) -> tuple[BaseModel, LLMResponse]:
        schema_json = json.dumps(schema.model_json_schema(), indent=2)
        structured_system = (
            f"{system}\n\n"
            f"Respond ONLY with a valid JSON object matching this schema:\n"
            f"```json\n{schema_json}\n```"
        )
        resp = await self.generate(prompt, system=structured_system, temperature=temperature, max_tokens=max_tokens)
        parsed = self._parse_json(resp.content, schema)
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
        return len(text) // 4

    def _parse_json(self, content: str, schema: Type[BaseModel]) -> BaseModel:
        content = content.strip()
        candidates = [
            content,
            re.search(r"```(?:json)?\s*([\s\S]*?)```", content),
            re.search(r"\{[\s\S]*\}", content),
        ]
        for attempt in candidates:
            try:
                text = attempt.group(1).strip() if hasattr(attempt, "group") else (attempt or "")
                return schema.model_validate_json(text)
            except Exception:
                continue
        # Last resort: try to repair truncated JSON by closing open braces and strings
        for attempt in candidates:
            try:
                text = attempt.group(1).strip() if hasattr(attempt, "group") else (attempt or "")
                if not text:
                    continue
                # If we have an odd number of unescaped quotes, close the string
                quote_count = len(re.findall(r'(?<!\\)"', text))
                if quote_count % 2 != 0:
                    text += '"'
                # Count unclosed braces/brackets and close them
                opens = text.count('{') - text.count('}')
                opens_sq = text.count('[') - text.count(']')
                # Remove trailing comma before closing
                text = text.rstrip().rstrip(',')
                text = text + ']' * max(0, opens_sq) + '}' * max(0, opens)
                return schema.model_validate_json(text)
            except Exception:
                continue
        raise ValueError(f"Could not parse JSON from Groq response: {content[:300]}")
