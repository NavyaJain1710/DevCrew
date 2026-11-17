"""
Model Router — decides which LLM provider+model to use for each task type.

Task routing:
  REQUIREMENT_ANALYSIS  → primary (strong reasoning)
  ARCHITECTURE          → primary
  PLANNING              → primary
  CODING                → coding model
  DEBUGGING             → coding model (with primary fallback)
  TESTING               → coding model
  SECURITY              → primary
  REVIEW                → primary
  SUMMARIZATION         → fast model
  CLASSIFICATION        → fast model
  DOCUMENTATION         → fast model

Every routing decision is logged.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass
from typing import Optional

import structlog

from app.config import get_settings
from app.llm.base import LLMProvider

logger = structlog.get_logger(__name__)
settings = get_settings()


class TaskType(str, enum.Enum):
    REQUIREMENT_ANALYSIS = "REQUIREMENT_ANALYSIS"
    ARCHITECTURE = "ARCHITECTURE"
    PLANNING = "PLANNING"
    CODING = "CODING"
    DEBUGGING = "DEBUGGING"
    TESTING = "TESTING"
    SECURITY = "SECURITY"
    REVIEW = "REVIEW"
    SUMMARIZATION = "SUMMARIZATION"
    CLASSIFICATION = "CLASSIFICATION"
    DOCUMENTATION = "DOCUMENTATION"


class CostClass(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class RoutingDecision:
    provider: str
    model: str
    reason: str
    estimated_cost_class: CostClass
    task_type: TaskType


# ── Routing table ─────────────────────────────────────────────────────────────

_ROUTING_TABLE: dict[TaskType, tuple[str, str, CostClass, str]] = {
    # (provider, model, cost_class, reason)
    TaskType.REQUIREMENT_ANALYSIS: (
        settings.primary_provider,
        settings.primary_model,
        CostClass.HIGH,
        "Requirement analysis needs strong reasoning to detect ambiguities and structure specs accurately.",
    ),
    TaskType.ARCHITECTURE: (
        settings.primary_provider,
        settings.primary_model,
        CostClass.HIGH,
        "Architecture decisions require deep reasoning about trade-offs and system design.",
    ),
    TaskType.PLANNING: (
        settings.primary_provider,
        settings.primary_model,
        CostClass.HIGH,
        "Planning requires understanding of project state and dependency management.",
    ),
    TaskType.CODING: (
        settings.coding_provider,
        settings.coding_model,
        CostClass.MEDIUM,
        "Code generation is handled by a specialized coding model for better output quality.",
    ),
    TaskType.DEBUGGING: (
        settings.coding_provider,
        settings.coding_model,
        CostClass.MEDIUM,
        "Debugging uses the coding model; escalated to primary if not resolved after 2 retries.",
    ),
    TaskType.TESTING: (
        settings.coding_provider,
        settings.coding_model,
        CostClass.MEDIUM,
        "Test generation benefits from the coding model's understanding of code structure.",
    ),
    TaskType.SECURITY: (
        settings.primary_provider,
        settings.primary_model,
        CostClass.HIGH,
        "Security analysis requires nuanced reasoning beyond pattern matching.",
    ),
    TaskType.REVIEW: (
        settings.primary_provider,
        settings.primary_model,
        CostClass.HIGH,
        "Final code review needs broad reasoning about quality, security, and correctness.",
    ),
    TaskType.SUMMARIZATION: (
        settings.fast_provider,
        settings.fast_model,
        CostClass.LOW,
        "Summarization is a simple task; cheap/fast model reduces cost significantly.",
    ),
    TaskType.CLASSIFICATION: (
        settings.fast_provider,
        settings.fast_model,
        CostClass.LOW,
        "Classification is simple and deterministic; fast model is sufficient.",
    ),
    TaskType.DOCUMENTATION: (
        settings.fast_provider,
        settings.fast_model,
        CostClass.LOW,
        "Documentation generation is formatting-heavy; fast model handles it well.",
    ),
}


class ModelRouter:
    """Routes task types to appropriate LLM provider + model combinations."""

    def route(self, task_type: TaskType, retry_count: int = 0) -> RoutingDecision:
        """
        Return routing decision for a given task type.
        If retry_count > 0 for DEBUGGING, escalate to primary model.
        """
        provider, model, cost_class, reason = _ROUTING_TABLE[task_type]

        # Escalation: if debugging has failed twice, switch to primary reasoning model
        if task_type == TaskType.DEBUGGING and retry_count >= 2:
            provider = settings.primary_provider
            model = settings.primary_model
            cost_class = CostClass.HIGH
            reason = f"Debugging escalated to primary reasoning model after {retry_count} failed retries."

        decision = RoutingDecision(
            provider=provider,
            model=model,
            reason=reason,
            estimated_cost_class=cost_class,
            task_type=task_type,
        )

        logger.info(
            "model_routed",
            task_type=task_type.value,
            provider=provider,
            model=model,
            cost_class=cost_class.value,
            retry_count=retry_count,
        )

        return decision

    def get_provider(self, task_type: TaskType, retry_count: int = 0) -> LLMProvider:
        """Convenience method — returns a ready-to-use LLMProvider instance."""
        decision = self.route(task_type, retry_count)
        return _build_provider(decision.provider, decision.model)


def _build_provider(provider: str, model: str) -> LLMProvider:
    """Instantiate the correct provider class."""
    from app.llm.providers.groq import GroqProvider
    from app.llm.providers.openrouter import OpenRouterProvider
    from app.llm.providers.gemini import GeminiProvider

    if provider == "groq":
        return GroqProvider(model=model)
    elif provider == "openrouter":
        return OpenRouterProvider(model=model)
    elif provider == "gemini":
        return GeminiProvider(model=model)
    else:
        raise ValueError(f"Unknown LLM provider: '{provider}'. Supported: openrouter, groq, gemini.")


# Singleton router instance
model_router = ModelRouter()
