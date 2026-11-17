"""
A2A (Agent-to-Agent) Protocol Server Router.

Satisfies Requirement 6:
- Exposes Google ADK agent through official A2A protocol
- Publishes Agent Card at /.well-known/agent.json
- Handles task lifecycle operations (submit, status query, cancel)
- Validates incoming and outgoing payloads
- Persists provenance linking originating execution to A2A task
"""

from __future__ import annotations

import asyncio
import uuid
from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException, status
import structlog

from app.a2a.models import (
    A2ATaskResponse,
    A2ATaskSubmitRequest,
    AgentCard,
    AgentSkill,
    utc_now_iso,
)
from app.adk.agent import google_adk_agent

logger = structlog.get_logger(__name__)

router = APIRouter(tags=["A2A Protocol"])

# In-memory A2A task registry with provenance tracking
_TASK_STORE: Dict[str, Dict[str, Any]] = {}


def get_agent_card() -> AgentCard:
    """Construct the official Agent Card for the Google ADK Developer Agent."""
    return AgentCard(
        id="google-adk-developer",
        name="Google ADK Developer Agent",
        version="2.12.0",
        description=(
            "Autonomous Software Engineer agent built with Google Agent Development Kit (ADK). "
            "Implements software features, interacts with MCP tools, and verifies code in sandbox."
        ),
        endpoints={
            "agent_card": "/.well-known/agent.json",
            "tasks": "/api/a2a/tasks",
        },
        skills=[
            AgentSkill(
                id="code_implementation",
                name="Software Code Implementation & Testing",
                description="Generates production application code and automated tests using MCP tools.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "raw_requirement": {"type": "string"},
                        "architecture": {"type": "object"},
                        "requirements": {"type": "object"},
                        "workspace_path": {"type": "string"},
                    },
                    "required": ["raw_requirement", "workspace_path"],
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "status": {"type": "string"},
                        "files_created": {"type": "array", "items": {"type": "string"}},
                        "test_summary": {"type": "object"},
                    },
                },
                tags=["coding", "google-adk", "mcp", "testing"],
            )
        ],
    )


# ─── A2A Discovery Endpoints ──────────────────────────────────────────────────

@router.get("/.well-known/agent.json", response_model=AgentCard, summary="A2A Agent Card Discovery")
@router.get("/api/a2a/agent-card", response_model=AgentCard, summary="A2A Agent Card")
async def get_a2a_agent_card() -> AgentCard:
    """Return the official A2A Agent Card metadata."""
    return get_agent_card()


# ─── A2A Task Management Operations ───────────────────────────────────────────

@router.post(
    "/api/a2a/tasks",
    response_model=A2ATaskResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Submit A2A Task to Google ADK Agent",
)
async def submit_a2a_task(req: A2ATaskSubmitRequest) -> A2ATaskResponse:
    """
    Accept an A2A task delegation request from CrewAI.
    Validates input schema and executes task asynchronously.
    """
    task_id = f"a2a-{uuid.uuid4().hex[:12]}"
    now = utc_now_iso()

    task_record = {
        "task_id": task_id,
        "status": "working",
        "skill_id": req.skill_id,
        "created_at": now,
        "updated_at": now,
        "execution_id": req.execution_id,
        "origin_framework": req.origin_framework,
        "input_payload": req.input_payload,
        "output_payload": None,
        "error": None,
        "provenance": {
            "origin_framework": req.origin_framework,
            "target_framework": "Google ADK",
            "execution_id": req.execution_id,
            "session_id": req.session_id,
        },
    }
    _TASK_STORE[task_id] = task_record
    logger.info("a2a_task_submitted", task_id=task_id, execution_id=req.execution_id)

    # Execute task synchronously or asynchronously
    # Run the Google ADK agent execution in background or directly
    try:
        enriched_payload = dict(req.input_payload)
        enriched_payload.setdefault("execution_id", req.execution_id)
        output = await google_adk_agent.execute_task(
            task_id=task_id,
            input_payload=enriched_payload,
        )
        task_record["status"] = "completed"
        task_record["output_payload"] = output
        task_record["updated_at"] = utc_now_iso()

        if output and ("prompt_tokens" in output or "completion_tokens" in output):
            from app.observability.tracer import observability
            observability.record_tokens(
                req.execution_id,
                output.get("prompt_tokens", 0),
                output.get("completion_tokens", 0),
            )
    except Exception as e:
        logger.error("a2a_task_execution_failed", task_id=task_id, error=str(e))
        task_record["status"] = "failed"
        task_record["error"] = str(e)
        task_record["updated_at"] = utc_now_iso()

    return A2ATaskResponse(**task_record)


@router.get(
    "/api/a2a/tasks/{task_id}",
    response_model=A2ATaskResponse,
    summary="Get A2A Task Status and Output",
)
async def get_a2a_task(task_id: str) -> A2ATaskResponse:
    """Retrieve task status and result by A2A task identifier."""
    record = _TASK_STORE.get(task_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"A2A task '{task_id}' not found.",
        )
    return A2ATaskResponse(**record)


@router.post(
    "/api/a2a/tasks/{task_id}/cancel",
    response_model=A2ATaskResponse,
    summary="Cancel A2A Task",
)
async def cancel_a2a_task(task_id: str) -> A2ATaskResponse:
    """Cancel a running A2A task."""
    record = _TASK_STORE.get(task_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"A2A task '{task_id}' not found.",
        )
    record["status"] = "canceled"
    record["updated_at"] = utc_now_iso()
    return A2ATaskResponse(**record)
