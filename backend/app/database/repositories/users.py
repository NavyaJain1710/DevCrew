"""User repository — all database operations for the User model."""

from __future__ import annotations

import uuid
from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import User, UserRole


class UserRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        result = await self._db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self._db.execute(
            select(User).where(User.email == email.lower())
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        email: str,
        hashed_password: str,
        full_name: str,
        role: UserRole = UserRole.USER,
    ) -> User:
        user = User(
            email=email.lower(),
            hashed_password=hashed_password,
            full_name=full_name,
            role=role,
        )
        self._db.add(user)
        await self._db.flush()
        await self._db.refresh(user)
        return user

    async def list_all(self, limit: int = 100, offset: int = 0) -> Sequence[User]:
        result = await self._db.execute(
            select(User).order_by(User.created_at.desc()).limit(limit).offset(offset)
        )
        return result.scalars().all()

    async def count(self) -> int:
        from sqlalchemy import func
        result = await self._db.execute(select(func.count(User.id)))
        return result.scalar_one()

    async def update_active(self, user_id: uuid.UUID, is_active: bool) -> Optional[User]:
        user = await self.get_by_id(user_id)
        if user:
            user.is_active = is_active
            await self._db.flush()
            await self._db.refresh(user)
        return user
