"""
A2A (Agent-to-Agent) Protocol Models — Discovery, Agent Card, & Task Management.

Adheres to official A2A protocol specifications:
- Agent Card metadata hosted at /.well-known/agent.json
- Managed task lifecycle: submitted -> working -> completed / failed / canceled
- Strict input/output validation and provenance tracing
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ─── Agent Card & Discovery Models ────────────────────────────────────────────

class AgentSkill(BaseModel):
    id: str
    name: str
    description: str
    input_schema: Dict[str, Any] = Field(default_factory=dict)
    output_schema: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)


class AgentAuthentication(BaseModel):
    type: str = "Bearer"
    description: str = "JWT bearer token or API key required"


class AgentCard(BaseModel):
    """
    Standardized A2A Agent Card metadata document.
    Enables autonomous discovery of Google ADK capabilities by external orchestrators.
    """
    id: str = "google-adk-devcrew-developer"
    name: str = "Google ADK Developer Agent"
    version: str = "2.12.0"
    framework: str = "Google Agent Development Kit (ADK)"
    description: str = (
        "Production software engineering agent powered by Google ADK. "
        "Implements modular code, executes MCP tools, and runs sandbox verification."
    )
    endpoints: Dict[str, str] = Field(
        default_factory=lambda: {
            "agent_card": "/.well-known/agent.json",
            "tasks": "/api/a2a/tasks",
        }
    )
    authentication: AgentAuthentication = Field(default_factory=AgentAuthentication)
    skills: List[AgentSkill] = Field(default_factory=list)


# ─── Task Delegation Models ───────────────────────────────────────────────────

class A2ATaskSubmitRequest(BaseModel):
    """Payload sent by CrewAI to delegate a task to the Google ADK agent."""
    skill_id: str = "code_implementation"
    session_id: Optional[str] = None
    execution_id: str
    origin_framework: str = "CrewAI"
    input_payload: Dict[str, Any]
    metadata: Dict[str, Any] = Field(default_factory=dict)


class A2ATaskResponse(BaseModel):
    """A2A task status and output response."""
    task_id: str
    status: str = "submitted"  # submitted | working | completed | failed | canceled
    skill_id: str
    created_at: str = Field(default_factory=utc_now_iso)
    updated_at: str = Field(default_factory=utc_now_iso)
    output_payload: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    provenance: Dict[str, Any] = Field(default_factory=dict)
