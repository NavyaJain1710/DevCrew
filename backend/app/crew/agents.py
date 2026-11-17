"""
CrewAI Agents for DevCrew Orchestration.

Satisfies Requirements 4 & 7:
- Uses official CrewAI Agent constructs
- Distinct roles: Requirement Analyst, Software Architect, Planner, Quality Sentinel
- Integrates with A2A client to delegate implementation to Google ADK
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from crewai import Agent, LLM
import structlog

from app.a2a.client import a2a_client
from app.config import get_settings
from app.llm.router import TaskType, model_router
from app.mcp.client import mcp_client

logger = structlog.get_logger(__name__)
settings = get_settings()


def _get_crew_llm() -> LLM:
    """Provide configured CrewAI LLM pointing to Groq's OpenAI-compatible endpoint."""
    import os
    base_url = settings.groq_base_url or "https://api.groq.com/openai/v1"
    api_key = settings.groq_api_key or os.getenv("GROQ_API_KEY") or ""

    if not api_key:
        logger.error("crew_llm_no_api_key", msg="GROQ_API_KEY is not set! Agents will fail.")
        api_key = "missing-groq-key"

    # Always ensure OPENAI_API_KEY is in environment for CrewAI native provider check
    if not os.environ.get("OPENAI_API_KEY"):
        os.environ["OPENAI_API_KEY"] = api_key
    if not os.environ.get("OPENAI_API_BASE"):
        os.environ["OPENAI_API_BASE"] = base_url

    # Use primary_model from settings, but strip any "openai/" prefix for Groq
    model_name = settings.primary_model
    # Remove provider prefix if present (e.g. "openai/gpt-oss-20b" -> "gpt-oss-20b")
    # For Groq, we use "groq/<model>" format for CrewAI LLM
    if "/" in model_name:
        # Keep the model as-is if it's a known path, otherwise strip provider prefix
        bare_name = model_name.split("/", 1)[1]
    else:
        bare_name = model_name

    # CrewAI uses "groq/<model>" to route via LiteLLM to Groq
    crew_model = f"groq/{bare_name}"

    try:
        return LLM(
            model=crew_model,
            api_key=api_key,
            temperature=0.2,
        )
    except Exception as e:
        logger.warning("crew_llm_setup_error", error=str(e), model=crew_model)
        # Hardcoded safe fallback — llama-3.3-70b is free on Groq
        return LLM(
            model="groq/llama-3.3-70b-versatile",
            api_key=api_key,
            temperature=0.2,
        )


def create_requirement_analyst_agent() -> Agent:
    """CrewAI agent for requirement engineering and specification."""
    return Agent(
        role="Senior Requirement Analyst",
        goal="Deconstruct natural language user requirements into detailed, unambiguous specifications.",
        backstory=(
            "You are a principal business systems analyst with 15 years of experience. "
            "You extract functional requirements, non-functional requirements, acceptance criteria, "
            "and user personas, eliminating ambiguity before software design begins."
        ),
        verbose=True,
        allow_delegation=False,
        llm=_get_crew_llm(),
    )


def create_software_architect_agent() -> Agent:
    """CrewAI agent for technical architecture and data modeling."""
    return Agent(
        role="Principal Software Architect",
        goal="Design robust, scalable system architectures, API schemas, and data models.",
        backstory=(
            "You are an elite software architect who champions clean architecture, "
            "SOLID principles, security-by-design, and modular RESTful APIs. "
            "You design practical schemas and clear module boundaries."
        ),
        verbose=True,
        allow_delegation=False,
        llm=_get_crew_llm(),
    )


def create_engineering_planner_agent() -> Agent:
    """CrewAI agent for task planning, dependencies, and delegation."""
    return Agent(
        role="Engineering Project Lead",
        goal="Formulate sequential task dependency graphs and delegate tasks via A2A protocol.",
        backstory=(
            "You are a technical delivery lead coordinating multi-agent workflows. "
            "You structure tasks with clear acceptance criteria and delegate code synthesis "
            "to specialist agents via the A2A protocol."
        ),
        verbose=True,
        allow_delegation=True,
        llm=_get_crew_llm(),
    )


def create_quality_sentinel_agent() -> Agent:
    """CrewAI agent for security scanning, linting, and comprehensive review."""
    return Agent(
        role="Principal Quality & Security Auditor",
        goal="Rigourously inspect generated code for security vulnerabilities, OWASP flaws, and code smell.",
        backstory=(
            "You are a DevSecOps auditor. You review code for SQL injection, path traversal, "
            "secret leakage, and code quality. You only approve implementations that pass all safety bars."
        ),
        verbose=True,
        allow_delegation=False,
        llm=_get_crew_llm(),
    )
