"""
DevCrew — SQLAlchemy ORM Models

All tables defined here. Alembic reads this file for migrations.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


# ─── Enums ────────────────────────────────────────────────────────────────────

import enum


class UserRole(str, enum.Enum):
    USER = "USER"
    ADMIN = "ADMIN"


class ProjectStatus(str, enum.Enum):
    CREATED = "CREATED"
    ANALYZING = "ANALYZING"
    ARCHITECTING = "ARCHITECTING"
    IMPLEMENTING = "IMPLEMENTING"
    TESTING = "TESTING"
    FIXING = "FIXING"
    SECURITY_SCANNING = "SECURITY_SCANNING"
    REVIEWING = "REVIEWING"
    DOCUMENTING = "DOCUMENTING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    PAUSED = "PAUSED"
    WAITING_FOR_APPROVAL = "WAITING_FOR_APPROVAL"


class AgentName(str, enum.Enum):
    MANAGER = "manager"
    REQUIREMENT = "requirement"
    ARCHITECT = "architect"
    DEVELOPER = "developer"
    TESTER = "tester"
    SECURITY = "security"
    REVIEWER = "reviewer"
    DOCUMENTATION = "documentation"


class TaskStatus(str, enum.Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"


class ApprovalStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


# ─── Models ───────────────────────────────────────────────────────────────────


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole), nullable=False, default=UserRole.USER
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Relationships
    projects: Mapped[list[Project]] = relationship(
        "Project", back_populates="owner", cascade="all, delete-orphan"
    )

    __table_args__ = (Index("ix_users_email", "email"),)


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    raw_requirement: Mapped[str] = mapped_column(Text, nullable=False, default="")
    status: Mapped[ProjectStatus] = mapped_column(
        Enum(ProjectStatus), nullable=False, default=ProjectStatus.CREATED
    )
    iteration_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    workspace_path: Mapped[str] = mapped_column(String(512), nullable=True)
    error_message: Mapped[str] = mapped_column(Text, nullable=True)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    # Cost tracking
    total_prompt_tokens: Mapped[int] = mapped_column(BigInteger, default=0)
    total_completion_tokens: Mapped[int] = mapped_column(BigInteger, default=0)
    estimated_cost_usd: Mapped[float] = mapped_column(Float, default=0.0)

    # Relationships
    owner: Mapped[User] = relationship("User", back_populates="projects")
    requirements: Mapped[list[ProjectRequirement]] = relationship(
        "ProjectRequirement", back_populates="project", cascade="all, delete-orphan"
    )
    architectures: Mapped[list[Architecture]] = relationship(
        "Architecture", back_populates="project", cascade="all, delete-orphan"
    )
    tasks: Mapped[list[AgentTask]] = relationship(
        "AgentTask", back_populates="project", cascade="all, delete-orphan"
    )
    agent_messages: Mapped[list[AgentMessage]] = relationship(
        "AgentMessage", back_populates="project", cascade="all, delete-orphan"
    )
    file_changes: Mapped[list[FileChange]] = relationship(
        "FileChange", back_populates="project", cascade="all, delete-orphan"
    )
    test_runs: Mapped[list[TestRun]] = relationship(
        "TestRun", back_populates="project", cascade="all, delete-orphan"
    )
    security_scans: Mapped[list[SecurityScan]] = relationship(
        "SecurityScan", back_populates="project", cascade="all, delete-orphan"
    )
    review_results: Mapped[list[ReviewResult]] = relationship(
        "ReviewResult", back_populates="project", cascade="all, delete-orphan"
    )
    model_usages: Mapped[list[ModelUsage]] = relationship(
        "ModelUsage", back_populates="project", cascade="all, delete-orphan"
    )
    artifacts: Mapped[list[ProjectArtifact]] = relationship(
        "ProjectArtifact", back_populates="project", cascade="all, delete-orphan"
    )
    github_repos: Mapped[list[GitHubRepo]] = relationship(
        "GitHubRepo", back_populates="project", cascade="all, delete-orphan"
    )
    approval_requests: Mapped[list[HumanApprovalRequest]] = relationship(
        "HumanApprovalRequest", back_populates="project", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_projects_user_id", "user_id"),
        Index("ix_projects_status", "status"),
    )


class ProjectRequirement(Base):
    __tablename__ = "project_requirements"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    structured_data: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    raw_text: Mapped[str] = mapped_column(Text, nullable=True)
    is_approved: Mapped[bool] = mapped_column(Boolean, default=False)

    project: Mapped[Project] = relationship("Project", back_populates="requirements")


class Architecture(Base):
    __tablename__ = "architectures"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    system_design: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    database_schema: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    api_specification: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    folder_structure: Mapped[str] = mapped_column(Text, nullable=True)
    technology_choices: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    is_approved: Mapped[bool] = mapped_column(Boolean, default=False)

    project: Mapped[Project] = relationship("Project", back_populates="architectures")


class AgentTask(Base):
    __tablename__ = "agent_tasks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    agent: Mapped[AgentName] = mapped_column(Enum(AgentName), nullable=False)
    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus), nullable=False, default=TaskStatus.PENDING
    )
    objective: Mapped[str] = mapped_column(Text, nullable=False, default="")
    input_data: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    output_data: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=True)
    error_message: Mapped[str] = mapped_column(Text, nullable=True)
    iteration: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=True)

    project: Mapped[Project] = relationship("Project", back_populates="tasks")
    file_changes: Mapped[list[FileChange]] = relationship(
        "FileChange", back_populates="task"
    )

    __table_args__ = (Index("ix_agent_tasks_project_id", "project_id"),)


class AgentMessage(Base):
    __tablename__ = "agent_messages"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    from_agent: Mapped[str] = mapped_column(String(50), nullable=False)
    to_agent: Mapped[str] = mapped_column(String(50), nullable=False)
    message_type: Mapped[str] = mapped_column(String(100), nullable=False)
    priority: Mapped[str] = mapped_column(String(20), nullable=False, default="normal")
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)

    project: Mapped[Project] = relationship("Project", back_populates="agent_messages")

    __table_args__ = (Index("ix_agent_messages_project_id", "project_id"),)


class FileChange(Base):
    __tablename__ = "file_changes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    task_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agent_tasks.id", ondelete="SET NULL"),
        nullable=True,
    )
    file_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    change_type: Mapped[str] = mapped_column(String(20), nullable=False)  # created|modified|deleted
    before_content: Mapped[str] = mapped_column(Text, nullable=True)
    after_content: Mapped[str] = mapped_column(Text, nullable=True)
    reason: Mapped[str] = mapped_column(Text, nullable=True)
    agent: Mapped[str] = mapped_column(String(50), nullable=True)
    lines_added: Mapped[int] = mapped_column(Integer, default=0)
    lines_removed: Mapped[int] = mapped_column(Integer, default=0)

    project: Mapped[Project] = relationship("Project", back_populates="file_changes")
    task: Mapped[AgentTask] = relationship("AgentTask", back_populates="file_changes")

    __table_args__ = (Index("ix_file_changes_project_id", "project_id"),)


class TestRun(Base):
    __tablename__ = "test_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    task_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agent_tasks.id", ondelete="SET NULL"),
        nullable=True,
    )
    iteration: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    overall_status: Mapped[str] = mapped_column(String(20), nullable=False)  # passed|failed|error
    passed: Mapped[int] = mapped_column(Integer, default=0)
    failed: Mapped[int] = mapped_column(Integer, default=0)
    skipped: Mapped[int] = mapped_column(Integer, default=0)
    coverage_percent: Mapped[float] = mapped_column(Float, default=0.0)
    execution_time_ms: Mapped[int] = mapped_column(Integer, default=0)
    raw_output: Mapped[str] = mapped_column(Text, nullable=True)
    failures: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False, default=list)
    recommendations: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)

    project: Mapped[Project] = relationship("Project", back_populates="test_runs")

    __table_args__ = (Index("ix_test_runs_project_id", "project_id"),)


class SecurityScan(Base):
    __tablename__ = "security_scans"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    scanner: Mapped[str] = mapped_column(String(50), nullable=False)  # bandit|semgrep|pip-audit|combined
    critical_count: Mapped[int] = mapped_column(Integer, default=0)
    high_count: Mapped[int] = mapped_column(Integer, default=0)
    medium_count: Mapped[int] = mapped_column(Integer, default=0)
    low_count: Mapped[int] = mapped_column(Integer, default=0)
    findings: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False, default=list)
    raw_output: Mapped[str] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="completed")

    project: Mapped[Project] = relationship("Project", back_populates="security_scans")

    __table_args__ = (Index("ix_security_scans_project_id", "project_id"),)


class ReviewResult(Base):
    __tablename__ = "review_results"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(30), nullable=False
    )  # approved|changes_required
    overall_score: Mapped[float] = mapped_column(Float, default=0.0)
    code_quality_score: Mapped[float] = mapped_column(Float, default=0.0)
    architecture_score: Mapped[float] = mapped_column(Float, default=0.0)
    security_score: Mapped[float] = mapped_column(Float, default=0.0)
    testing_score: Mapped[float] = mapped_column(Float, default=0.0)
    documentation_score: Mapped[float] = mapped_column(Float, default=0.0)
    strengths: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    issues: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False, default=list)
    recommendations: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)

    project: Mapped[Project] = relationship("Project", back_populates="review_results")


class ModelUsage(Base):
    __tablename__ = "model_usages"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=True,
    )
    agent: Mapped[str] = mapped_column(String(50), nullable=False)
    model: Mapped[str] = mapped_column(String(150), nullable=False)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    task_type: Mapped[str] = mapped_column(String(50), nullable=False)
    prompt_tokens: Mapped[int] = mapped_column(Integer, default=0)
    completion_tokens: Mapped[int] = mapped_column(Integer, default=0)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    estimated_cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    success: Mapped[bool] = mapped_column(Boolean, default=True)
    error_message: Mapped[str] = mapped_column(Text, nullable=True)

    project: Mapped[Project] = relationship("Project", back_populates="model_usages")

    __table_args__ = (Index("ix_model_usages_project_id", "project_id"),)


class ProjectArtifact(Base):
    __tablename__ = "project_artifacts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    artifact_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # zip|pdf|readme|report
    file_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, default=0)
    download_count: Mapped[int] = mapped_column(Integer, default=0)

    project: Mapped[Project] = relationship("Project", back_populates="artifacts")


class GitHubRepo(Base):
    __tablename__ = "github_repos"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    repo_name: Mapped[str] = mapped_column(String(255), nullable=False)
    repo_url: Mapped[str] = mapped_column(String(512), nullable=True)
    branch: Mapped[str] = mapped_column(String(100), nullable=False, default="main")
    last_push_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    pr_url: Mapped[str] = mapped_column(String(512), nullable=True)

    project: Mapped[Project] = relationship("Project", back_populates="github_repos")


class HumanApprovalRequest(Base):
    __tablename__ = "human_approval_requests"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    context_data: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    status: Mapped[ApprovalStatus] = mapped_column(
        Enum(ApprovalStatus), nullable=False, default=ApprovalStatus.PENDING
    )
    resolved_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    resolved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    rejection_reason: Mapped[str] = mapped_column(Text, nullable=True)

    project: Mapped[Project] = relationship("Project", back_populates="approval_requests")

    __table_args__ = (
        Index("ix_approval_requests_project_id", "project_id"),
        Index("ix_approval_requests_status", "status"),
    )


    
