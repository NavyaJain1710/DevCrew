"""Approval repository — CRUD for human approval requests."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import ApprovalStatus, HumanApprovalRequest


class ApprovalRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_by_id(self, approval_id: uuid.UUID) -> Optional[HumanApprovalRequest]:
        result = await self._db.execute(
            select(HumanApprovalRequest).where(HumanApprovalRequest.id == approval_id)
        )
        return result.scalar_one_or_none()

    async def get_pending_for_project(self, project_id: uuid.UUID) -> list[HumanApprovalRequest]:
        result = await self._db.execute(
            select(HumanApprovalRequest).where(
                HumanApprovalRequest.project_id == project_id,
                HumanApprovalRequest.status == ApprovalStatus.PENDING,
            )
        )
        return list(result.scalars().all())

    async def create(
        self,
        project_id: uuid.UUID,
        action: str,
        description: str,
        context_data: dict,
    ) -> HumanApprovalRequest:
        req = HumanApprovalRequest(
            project_id=project_id,
            action=action,
            description=description,
            context_data=context_data,
            status=ApprovalStatus.PENDING,
        )
        self._db.add(req)
        await self._db.flush()
        await self._db.refresh(req)
        return req

    async def resolve(
        self,
        approval_id: uuid.UUID,
        status: ApprovalStatus,
        resolved_by: uuid.UUID,
        rejection_reason: Optional[str] = None,
    ) -> Optional[HumanApprovalRequest]:
        req = await self.get_by_id(approval_id)
        if req:
            req.status = status
            req.resolved_by = resolved_by
            req.resolved_at = datetime.utcnow()
            req.rejection_reason = rejection_reason
            await self._db.flush()
            await self._db.refresh(req)
        return req
