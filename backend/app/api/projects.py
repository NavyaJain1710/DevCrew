"""
Projects API — CRUD for projects plus sub-resources.
"""

from __future__ import annotations

import os
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, status, Response
from pydantic import BaseModel, Field

from app.database.models import (
    Project,
    ProjectStatus,
    ReviewResult,
    SecurityScan,
    TestRun,
)
from app.database.repositories.projects import ProjectRepository
from app.dependencies import CurrentUser, DBSession
from app.services.orchestrator import DevCrewOrchestrator

router = APIRouter(prefix="/projects", tags=["Projects"])


# ── Schemas ───────────────────────────────────────────────────────────────────


class CreateProjectRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str = Field(default="", max_length=2000)
    raw_requirement: str = Field(..., min_length=10)


class ProjectSummary(BaseModel):
    id: str
    name: str
    description: str
    status: str
    iteration_count: int
    estimated_cost_usd: float
    total_prompt_tokens: int
    total_completion_tokens: int
    created_at: datetime
    completed_at: Optional[datetime]

    model_config = {"from_attributes": True}


class ProjectDetail(ProjectSummary):
    raw_requirement: str
    workspace_path: Optional[str]
    error_message: Optional[str]
    requirements: Optional[dict] = None
    architecture: Optional[dict] = None
    pending_approval: Optional[dict] = None


class RunProjectResponse(BaseModel):
    project_id: str
    status: str
    message: str


class ApprovalRequest(BaseModel):
    approved: bool
    rejection_reason: Optional[str] = None


# ── Helper ────────────────────────────────────────────────────────────────────


def _project_to_summary(p: Project) -> ProjectSummary:
    return ProjectSummary(
        id=str(p.id),
        name=p.name,
        description=p.description,
        status=p.status.value,
        iteration_count=p.iteration_count,
        estimated_cost_usd=p.estimated_cost_usd,
        total_prompt_tokens=p.total_prompt_tokens,
        total_completion_tokens=p.total_completion_tokens,
        created_at=p.created_at,
        completed_at=p.completed_at,
    )


# ── Endpoints ─────────────────────────────────────────────────────────────────


@router.get("", response_model=list[ProjectSummary], summary="List user's projects")
async def list_projects(
    current_user: CurrentUser,
    db: DBSession,
    limit: int = 50,
    offset: int = 0,
) -> list[ProjectSummary]:
    repo = ProjectRepository(db)
    projects = await repo.get_by_user(current_user.id, limit=limit, offset=offset)
    return [_project_to_summary(p) for p in projects]


@router.post(
    "",
    response_model=ProjectSummary,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new project",
)
async def create_project(
    body: CreateProjectRequest,
    current_user: CurrentUser,
    db: DBSession,
) -> ProjectSummary:
    repo = ProjectRepository(db)
    project = await repo.create(
        user_id=current_user.id,
        name=body.name,
        description=body.description,
        raw_requirement=body.raw_requirement,
    )
    return _project_to_summary(project)


def _enrich_architecture(arch: Optional[Dict[str, Any]], workspace_path: Optional[str], raw_requirement: str) -> Optional[Dict[str, Any]]:
    if not arch and not workspace_path:
        return None
    
    result = dict(arch or {})
    
    # 1. Architecture Overview
    if not result.get("architecture_overview") or result.get("architecture_overview") == "FastAPI Layered Service Architecture":
        result["architecture_overview"] = (
            f"Layered Asynchronous Microservice Architecture tailored for: '{raw_requirement}'. "
            "Implements decoupled API routers, Pydantic v2 domain schemas, service-layer business logic, and automated test fixtures."
        )

    # 2. Technology Decisions / Tech Stack
    if not result.get("technology_decisions"):
        tech_list = result.get("tech_stack") or ["FastAPI", "Pydantic v2", "Pytest", "JWT Auth", "SQLite/PostgreSQL"]
        decision_map = {
            "fastapi": ("REST API Gateway", "High-performance asynchronous ASGI framework with automated OpenAPI and Swagger UI."),
            "pydantic": ("Data Validation & Typing", "Enforces strict type safety, input sanitization, and response serialization."),
            "pytest": ("Test Automation & TDD", "Provides test assertion introspection, fixture isolation, and regression verification."),
            "jwt": ("Stateless Authentication", "Secure bearer token generation for authenticated session tracking and RBAC."),
            "sqlite": ("Persistence Engine", "Lightweight ACID-compliant storage for application entities."),
            "postgres": ("Relational Database", "Scalable transactional database supporting ACID constraints."),
            "sqlalchemy": ("ORM Layer", "Asynchronous object-relational mapping preventing SQL injection."),
        }
        decisions = []
        for t in tech_list:
            t_lower = t.lower()
            matched = False
            for k, (purpose, reason) in decision_map.items():
                if k in t_lower:
                    decisions.append({"technology": t, "purpose": purpose, "reason": reason})
                    matched = True
                    break
            if not matched:
                decisions.append({"technology": t, "purpose": "Core Dependency", "reason": "Standard ecosystem component for application runtime."})
        result["technology_decisions"] = decisions

    # 3. Workspace Inspection for Folder Structure, API Endpoints, and Database Models
    if workspace_path and os.path.exists(workspace_path):
        root = Path(workspace_path)
        
        # Real folder structure
        if not result.get("folder_structure"):
            lines = []
            for p in sorted(root.rglob("*")):
                if any(x in p.parts for x in (".git", "__pycache__", ".pytest_cache", "venv", ".devcrew_artifacts")):
                    continue
                rel = p.relative_to(root)
                depth = len(rel.parts) - 1
                indent = "  " * depth
                prefix = "📁 " if p.is_dir() else "📄 "
                lines.append(f"{indent}{prefix}{rel.name}")
            if lines:
                result["folder_structure"] = "\n".join(lines)

        # Real API Endpoints from generated routers
        if not result.get("api_endpoints"):
            endpoints = []
            for py_file in root.rglob("*.py"):
                if "test" in py_file.name or "__pycache__" in str(py_file):
                    continue
                try:
                    content = py_file.read_text(errors="ignore")
                    matches = re.findall(r'@(?:app|router)\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']', content)
                    for method, path in matches:
                        stem = py_file.stem
                        prefix = f"/{stem}" if stem not in ("main", "app") and not path.startswith(f"/{stem}") else ""
                        full_path = f"{prefix}{path}" if prefix and not path.startswith(prefix) else path
                        endpoints.append({
                            "method": method.upper(),
                            "path": full_path,
                            "summary": f"{stem.capitalize()} operation",
                            "auth_required": "login" not in path and "register" not in path and "health" not in path
                        })
                except Exception:
                    pass
            if endpoints:
                result["api_endpoints"] = endpoints

        # Real Database Models from generated code
        if not result.get("database_tables") and not result.get("database_models"):
            models = []
            for py_file in root.rglob("*model*.py"):
                try:
                    content = py_file.read_text(errors="ignore")
                    matches = re.findall(r'class\s+([A-Za-z0-9_]+)\s*\(([^)]+)\):', content)
                    for cls_name, base in matches:
                        if "Enum" in base:
                            continue
                        models.append({
                            "name": cls_name,
                            "purpose": f"{cls_name} domain data model",
                            "columns": [{"name": "id", "type": "UUID/str"}, {"name": "data", "type": "JSON/Attributes"}]
                        })
                except Exception:
                    pass
            if models:
                result["database_tables"] = models

    # 4. Security Architecture
    if not result.get("security_architecture"):
        result["security_architecture"] = (
            "Implements JWT stateless authentication, strict Pydantic payload validation against injection, "
            "CORS policy restriction, and containerized workspace filesystem isolation."
        )

    return result


@router.get("/{project_id}", response_model=ProjectDetail, summary="Get project details")
async def get_project(
    project_id: uuid.UUID,
    current_user: CurrentUser,
    db: DBSession,
) -> ProjectDetail:
    repo = ProjectRepository(db)
    project = await repo.get_by_id(project_id, load_relations=True)
    _assert_ownership(project, current_user.id)
    
    req = project.requirements[-1].structured_data if project.requirements else None
    raw_arch = project.architectures[-1].system_design if project.architectures else None
    arch = _enrich_architecture(raw_arch, project.workspace_path, project.raw_requirement)
    
    approval = next((a for a in project.approval_requests if a.status.value == "PENDING"), None)
    pending_approval = {
        "id": str(approval.id),
        "action": approval.action,
        "description": approval.description,
    } if approval else None
    
    return ProjectDetail(
        id=str(project.id),
        name=project.name,
        description=project.description,
        status=project.status.value,
        iteration_count=project.iteration_count,
        estimated_cost_usd=project.estimated_cost_usd,
        total_prompt_tokens=project.total_prompt_tokens,
        total_completion_tokens=project.total_completion_tokens,
        created_at=project.created_at,
        completed_at=project.completed_at,
        raw_requirement=project.raw_requirement,
        workspace_path=project.workspace_path,
        error_message=project.error_message,
        requirements=req,
        architecture=arch,
        pending_approval=pending_approval,
    )


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    summary="Delete a project",
)
async def delete_project(
    project_id: uuid.UUID,
    current_user: CurrentUser,
    db: DBSession,
) -> None:
    repo = ProjectRepository(db)
    project = await repo.get_by_id(project_id)
    _assert_ownership(project, current_user.id)
    await repo.delete(project_id)


@router.post(
    "/{project_id}/run",
    response_model=RunProjectResponse,
    summary="Start the DevCrew agent pipeline for this project",
)
async def run_project(
    project_id: uuid.UUID,
    current_user: CurrentUser,
    db: DBSession,
    background_tasks: BackgroundTasks,
) -> RunProjectResponse:
    repo = ProjectRepository(db)
    project = await repo.get_by_id(project_id)
    _assert_ownership(project, current_user.id)

    # Reset error state and allow re-running from any finished or recoverable state
    project.error_message = None
    project.status = ProjectStatus.CREATED
    await db.commit()

    orchestrator = DevCrewOrchestrator()
    background_tasks.add_task(
        orchestrator.run,
        project_id=str(project_id),
        user_id=str(current_user.id),
    )

    return RunProjectResponse(
        project_id=str(project_id),
        status="started",
        message="DevCrew pipeline started. Connect to WebSocket for live updates.",
    )


@router.post(
    "/{project_id}/pause",
    response_model=RunProjectResponse,
    summary="Pause a running project",
)
async def pause_project(
    project_id: uuid.UUID,
    current_user: CurrentUser,
    db: DBSession,
) -> RunProjectResponse:
    repo = ProjectRepository(db)
    project = await repo.get_by_id(project_id)
    _assert_ownership(project, current_user.id)
    await repo.update_status(project_id, ProjectStatus.PAUSED)
    return RunProjectResponse(project_id=str(project_id), status="paused", message="Project paused.")


@router.post(
    "/{project_id}/cancel",
    response_model=RunProjectResponse,
    summary="Cancel a running project",
)
async def cancel_project(
    project_id: uuid.UUID,
    current_user: CurrentUser,
    db: DBSession,
) -> RunProjectResponse:
    repo = ProjectRepository(db)
    project = await repo.get_by_id(project_id)
    _assert_ownership(project, current_user.id)
    await repo.update_status(project_id, ProjectStatus.FAILED, error="Cancelled by user.")
    return RunProjectResponse(project_id=str(project_id), status="cancelled", message="Project cancelled.")


@router.post(
    "/{project_id}/approvals/{approval_id}",
    summary="Respond to a human-in-the-loop approval request",
)
async def respond_to_approval(
    project_id: uuid.UUID,
    approval_id: uuid.UUID,
    body: ApprovalRequest,
    current_user: CurrentUser,
    db: DBSession,
) -> dict:
    from app.database.repositories.approvals import ApprovalRepository
    from app.database.models import ApprovalStatus
    repo = ProjectRepository(db)
    project = await repo.get_by_id(project_id)
    _assert_ownership(project, current_user.id)

    approval_repo = ApprovalRepository(db)
    approval = await approval_repo.get_by_id(approval_id)
    if not approval or str(approval.project_id) != str(project_id):
        raise HTTPException(status_code=404, detail="Approval request not found.")

    new_status = ApprovalStatus.APPROVED if body.approved else ApprovalStatus.REJECTED
    await approval_repo.resolve(
        approval_id=approval_id,
        status=new_status,
        resolved_by=current_user.id,
        rejection_reason=body.rejection_reason,
    )

    from app.services.ws_hub import ws_hub
    await ws_hub.broadcast(
        project_id=str(project_id),
        event="approval_resolved",
        data={"approval_id": str(approval_id), "approved": body.approved},
    )

    return {"approval_id": str(approval_id), "status": new_status.value}


# ── Private ───────────────────────────────────────────────────────────────────


def _assert_ownership(project: Optional[Project], user_id: uuid.UUID) -> None:
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")
    if str(project.user_id) != str(user_id):
        raise HTTPException(status_code=403, detail="Access denied.")
