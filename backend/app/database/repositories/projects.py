"""Project repository — all database operations for the Project model."""

from __future__ import annotations

import uuid
from typing import Optional, Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.models import Project, ProjectStatus


class ProjectRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_by_id(
        self, project_id: uuid.UUID, load_relations: bool = False
    ) -> Optional[Project]:
        q = select(Project).where(Project.id == project_id)
        if load_relations:
            q = q.options(
                selectinload(Project.requirements),
                selectinload(Project.architectures),
                selectinload(Project.tasks),
                selectinload(Project.test_runs),
                selectinload(Project.security_scans),
                selectinload(Project.review_results),
                selectinload(Project.artifacts),
                selectinload(Project.approval_requests),
            )
        result = await self._db.execute(q)
        return result.scalar_one_or_none()

    async def get_by_user(
        self, user_id: uuid.UUID, limit: int = 50, offset: int = 0
    ) -> Sequence[Project]:
        result = await self._db.execute(
            select(Project)
            .where(Project.user_id == user_id)
            .order_by(Project.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()

    async def create(
        self,
        user_id: uuid.UUID,
        name: str,
        description: str,
        raw_requirement: str,
    ) -> Project:
        project = Project(
            user_id=user_id,
            name=name,
            description=description,
            raw_requirement=raw_requirement,
            status=ProjectStatus.CREATED,
        )
        self._db.add(project)
        await self._db.flush()
        await self._db.refresh(project)
        return project

    async def update_status(
        self, project_id: uuid.UUID, status: ProjectStatus, error: Optional[str] = None
    ) -> Optional[Project]:
        project = await self.get_by_id(project_id)
        if project:
            project.status = status
            if error:
                project.error_message = error
            await self._db.flush()
            await self._db.refresh(project)
        return project

    async def update_workspace(
        self, project_id: uuid.UUID, workspace_path: str
    ) -> Optional[Project]:
        project = await self.get_by_id(project_id)
        if project:
            project.workspace_path = workspace_path
            await self._db.flush()
            await self._db.refresh(project)
        return project

    async def increment_iteration(self, project_id: uuid.UUID) -> int:
        project = await self.get_by_id(project_id)
        if project:
            project.iteration_count += 1
            await self._db.flush()
            return project.iteration_count
        return 0

    async def add_token_usage(
        self,
        project_id: uuid.UUID,
        prompt_tokens: int,
        completion_tokens: int,
        cost_usd: float,
    ) -> None:
        project = await self.get_by_id(project_id)
        if project:
            project.total_prompt_tokens += prompt_tokens
            project.total_completion_tokens += completion_tokens
            project.estimated_cost_usd += cost_usd
            await self._db.flush()

    async def delete(self, project_id: uuid.UUID) -> bool:
        project = await self.get_by_id(project_id)
        if project:
            await self._db.delete(project)
            await self._db.flush()
            return True
        return False

    async def count_by_status(self, status: Optional[ProjectStatus] = None) -> int:
        q = select(func.count(Project.id))
        if status:
            q = q.where(Project.status == status)
        result = await self._db.execute(q)
        return result.scalar_one()

    async def list_all(
        self, limit: int = 100, offset: int = 0
    ) -> Sequence[Project]:
        result = await self._db.execute(
            select(Project)
            .order_by(Project.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()
