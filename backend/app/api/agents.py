"""Agents API — query agent runs, messages, and activity for a project."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.dependencies import CurrentUser, DBSession

router = APIRouter(prefix="/projects", tags=["Agents"])


class AgentRunResponse(BaseModel):
    id: str
    agent: str
    status: str
    objective: str
    iteration: int
    started_at: datetime | None
    finished_at: datetime | None
    duration_ms: int | None
    model_config = {"from_attributes": True}


class AgentMessageResponse(BaseModel):
    id: str
    from_agent: str
    to_agent: str
    message_type: str
    priority: str
    payload: dict[str, Any]
    timestamp: datetime
    model_config = {"from_attributes": True}


@router.get("/{project_id}/agents", response_model=list[AgentRunResponse])
async def get_agent_runs(
    project_id: uuid.UUID,
    current_user: CurrentUser,
    db: DBSession,
):
    from app.database.models import AgentTask
    from app.database.repositories.projects import ProjectRepository
    from sqlalchemy import select

    repo = ProjectRepository(db)
    project = await repo.get_by_id(project_id)
    if not project or str(project.user_id) != str(current_user.id):
        raise HTTPException(status_code=404, detail="Project not found.")

    result = await db.execute(
        select(AgentTask)
        .where(AgentTask.project_id == project_id)
        .order_by(AgentTask.created_at)
    )
    tasks = result.scalars().all()
    return [
        AgentRunResponse(
            id=str(t.id),
            agent=t.agent.value,
            status=t.status.value,
            objective=t.objective,
            iteration=t.iteration,
            started_at=t.started_at,
            finished_at=t.finished_at,
            duration_ms=t.duration_ms,
        )
        for t in tasks
    ]


@router.get("/{project_id}/activity", response_model=list[AgentMessageResponse])
async def get_agent_activity(
    project_id: uuid.UUID,
    current_user: CurrentUser,
    db: DBSession,
    limit: int = 100,
):
    from app.database.models import AgentMessage
    from app.database.repositories.projects import ProjectRepository
    from sqlalchemy import select

    repo = ProjectRepository(db)
    project = await repo.get_by_id(project_id)
    if not project or str(project.user_id) != str(current_user.id):
        raise HTTPException(status_code=404, detail="Project not found.")

    result = await db.execute(
        select(AgentMessage)
        .where(AgentMessage.project_id == project_id)
        .order_by(AgentMessage.created_at.desc())
        .limit(limit)
    )
    messages = result.scalars().all()
    return [
        AgentMessageResponse(
            id=str(m.id),
            from_agent=m.from_agent,
            to_agent=m.to_agent,
            message_type=m.message_type,
            priority=m.priority,
            payload=m.payload,
            timestamp=m.created_at,
        )
        for m in messages
    ]
