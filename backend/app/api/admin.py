"""Admin API — system-wide statistics and management (ADMIN role only)."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.dependencies import AdminUser, DBSession

router = APIRouter(prefix="/admin", tags=["Admin"])


class SystemStats(BaseModel):
    total_users: int
    total_projects: int
    active_runs: int
    completed_runs: int
    failed_runs: int
    total_model_calls: int
    total_cost_usd: float
    avg_test_coverage: float


@router.get("/stats", response_model=SystemStats)
async def get_system_stats(admin: AdminUser, db: DBSession):
    from sqlalchemy import func, select
    from app.database.models import (
        User, Project, ProjectStatus, ModelUsage, TestRun
    )

    total_users = (await db.execute(select(func.count(User.id)))).scalar_one()
    total_projects = (await db.execute(select(func.count(Project.id)))).scalar_one()
    active_runs = (
        await db.execute(
            select(func.count(Project.id)).where(
                Project.status.in_([
                    ProjectStatus.ANALYZING, ProjectStatus.IMPLEMENTING,
                    ProjectStatus.TESTING, ProjectStatus.REVIEWING,
                ])
            )
        )
    ).scalar_one()
    completed = (
        await db.execute(
            select(func.count(Project.id)).where(Project.status == ProjectStatus.COMPLETED)
        )
    ).scalar_one()
    failed = (
        await db.execute(
            select(func.count(Project.id)).where(Project.status == ProjectStatus.FAILED)
        )
    ).scalar_one()
    model_calls = (await db.execute(select(func.count(ModelUsage.id)))).scalar_one()
    total_cost = (await db.execute(select(func.sum(ModelUsage.estimated_cost_usd)))).scalar_one() or 0.0
    avg_coverage = (await db.execute(select(func.avg(TestRun.coverage_percent)))).scalar_one() or 0.0

    return SystemStats(
        total_users=total_users,
        total_projects=total_projects,
        active_runs=active_runs,
        completed_runs=completed,
        failed_runs=failed,
        total_model_calls=model_calls,
        total_cost_usd=round(total_cost, 4),
        avg_test_coverage=round(avg_coverage, 2),
    )


@router.get("/users")
async def list_users(admin: AdminUser, db: DBSession, limit: int = 100):
    from sqlalchemy import select
    from app.database.models import User

    result = await db.execute(select(User).order_by(User.created_at.desc()).limit(limit))
    users = result.scalars().all()
    return [
        {
            "id": str(u.id),
            "email": u.email,
            "full_name": u.full_name,
            "role": u.role.value,
            "is_active": u.is_active,
            "created_at": u.created_at.isoformat(),
        }
        for u in users
    ]


@router.get("/model-usage")
async def get_model_usage(admin: AdminUser, db: DBSession, limit: int = 500):
    from sqlalchemy import select
    from app.database.models import ModelUsage

    result = await db.execute(
        select(ModelUsage).order_by(ModelUsage.created_at.desc()).limit(limit)
    )
    usages = result.scalars().all()
    return [
        {
            "id": str(u.id),
            "project_id": str(u.project_id) if u.project_id else None,
            "agent": u.agent,
            "model": u.model,
            "provider": u.provider,
            "task_type": u.task_type,
            "prompt_tokens": u.prompt_tokens,
            "completion_tokens": u.completion_tokens,
            "latency_ms": u.latency_ms,
            "estimated_cost_usd": u.estimated_cost_usd,
            "success": u.success,
            "timestamp": u.created_at.isoformat(),
        }
        for u in usages
    ]


@router.get("/projects")
async def list_all_projects(admin: AdminUser, db: DBSession, limit: int = 100):
    from sqlalchemy import select
    from app.database.models import Project

    result = await db.execute(
        select(Project).order_by(Project.created_at.desc()).limit(limit)
    )
    projects = result.scalars().all()
    return [
        {
            "id": str(p.id),
            "user_id": str(p.user_id),
            "name": p.name,
            "status": p.status.value,
            "iteration_count": p.iteration_count,
            "estimated_cost_usd": p.estimated_cost_usd,
            "created_at": p.created_at.isoformat(),
            "completed_at": p.completed_at.isoformat() if p.completed_at else None,
        }
        for p in projects
    ]
