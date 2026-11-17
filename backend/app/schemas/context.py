"""
DevCrew Shared Execution Context — Typed Pydantic Models for State & Interoperability.

Satisfies Requirement 1 & Requirement 3:
- Full typed Pydantic models for execution context, intermediate states, and outputs
- Strict tenant/project workspace isolation
- Support for CrewAI, Google ADK, A2A, MCP, and RAG metadata
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ─── Enumerations ─────────────────────────────────────────────────────────────

class ExecutionStatus(str, Enum):
    INITIALIZED = "INITIALIZED"
    ANALYZING = "ANALYZING"
    ARCHITECTING = "ARCHITECTING"
    PLANNING = "PLANNING"
    DELEGATING_A2A = "DELEGATING_A2A"
    IMPLEMENTING = "IMPLEMENTING"
    TESTING = "TESTING"
    FIXING = "FIXING"
    SECURITY_SCANNING = "SECURITY_SCANNING"
    REVIEWING = "REVIEWING"
    DOCUMENTING = "DOCUMENTING"
    COMPLETED = "COMPLETED"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"
    PAUSED = "PAUSED"
    WAITING_FOR_APPROVAL = "WAITING_FOR_APPROVAL"


class FrameworkType(str, Enum):
    CREWAI = "CrewAI"
    GOOGLE_ADK = "Google ADK"
    A2A_BRIDGE = "A2A Protocol"


class TaskPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


# ─── Sub-models for Typed Context ─────────────────────────────────────────────

class AgentMessage(BaseModel):
    id: str = Field(default_factory=lambda: f"msg-{datetime.now(timezone.utc).timestamp()}")
    from_agent: str
    to_agent: str
    framework: FrameworkType = FrameworkType.CREWAI
    message_type: str = "task_assignment"  # task_assignment | status_update | artifact | feedback
    priority: TaskPriority = TaskPriority.NORMAL
    payload: Dict[str, Any] = Field(default_factory=dict)
    timestamp: str = Field(default_factory=utc_now_iso)


class TaskItem(BaseModel):
    task_id: str
    title: str
    assigned_agent: str
    assigned_framework: FrameworkType = FrameworkType.CREWAI
    objective: str
    dependencies: List[str] = Field(default_factory=list)
    status: str = "pending"  # pending | in_progress | completed | failed
    inputs: Dict[str, Any] = Field(default_factory=dict)
    output: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: str = Field(default_factory=utc_now_iso)
    completed_at: Optional[str] = None


class RAGReference(BaseModel):
    document_id: str
    title: str
    source_type: str  # documentation | pattern | standard | snippet
    content_snippet: str
    score: float = 1.0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ToolCallRecord(BaseModel):
    tool_name: str
    tool_server: str = "local_mcp"  # local_mcp | external_mcp
    arguments: Dict[str, Any] = Field(default_factory=dict)
    result_summary: str = ""
    success: bool = True
    error: Optional[str] = None
    duration_ms: float = 0.0
    timestamp: str = Field(default_factory=utc_now_iso)


class A2ATaskRecord(BaseModel):
    a2a_task_id: str
    initiator_framework: FrameworkType = FrameworkType.CREWAI
    target_framework: FrameworkType = FrameworkType.GOOGLE_ADK
    target_agent_id: str = "adk_developer_agent"
    target_skill_id: str = "code_implementation"
    status: str = "submitted"  # submitted | working | completed | failed | canceled
    input_payload: Dict[str, Any] = Field(default_factory=dict)
    output_payload: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: str = Field(default_factory=utc_now_iso)
    updated_at: str = Field(default_factory=utc_now_iso)


class TestFailureItem(BaseModel):
    test_name: str
    file: str
    line: Optional[int] = None
    error: str
    error_type: str = "assertion"
    severity: str = "high"
    suggested_area: str = ""


class TestRunMetrics(BaseModel):
    total: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    coverage_percent: float = 0.0
    duration_ms: float = 0.0
    failures: List[TestFailureItem] = Field(default_factory=list)
    tests_passed: bool = False


class SecurityScanFinding(BaseModel):
    title: str
    severity: str  # critical | high | medium | low | info
    file: str
    line: Optional[str] = None
    description: str
    impact: str = ""
    recommendation: str = ""
    scanner: str = "DevCrew Sentinel"
    status: str = "open"


class ReviewMetricScore(BaseModel):
    overall_score: float = 0.0
    code_quality_score: float = 0.0
    architecture_score: float = 0.0
    security_score: float = 0.0
    testing_score: float = 0.0
    documentation_score: float = 0.0
    approved: bool = False
    strengths: List[str] = Field(default_factory=list)
    issues: List[Dict[str, Any]] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)


# ─── Master Shared Execution Context ──────────────────────────────────────────

class ExecutionContext(BaseModel):
    """
    Typed, thread-safe, serializable execution context representing
    the complete state of a DevCrew pipeline run.
    """
    execution_id: str
    project_id: str
    user_id: str
    workspace_path: str

    # User Input & Security Status
    raw_requirement: str
    input_sanitized: bool = False
    security_flagged: bool = False
    security_flag_reason: Optional[str] = None

    # Pipeline lifecycle
    status: ExecutionStatus = ExecutionStatus.INITIALIZED
    current_stage: str = "initialization"
    current_framework: FrameworkType = FrameworkType.CREWAI
    iteration_count: int = 0
    max_iterations: int = 5
    started_at: str = Field(default_factory=utc_now_iso)
    updated_at: str = Field(default_factory=utc_now_iso)
    completed_at: Optional[str] = None

    # Intermediate agent artifacts
    requirements: Dict[str, Any] = Field(default_factory=dict)
    architecture: Dict[str, Any] = Field(default_factory=dict)
    task_plan: List[TaskItem] = Field(default_factory=list)
    retrieved_sources: List[RAGReference] = Field(default_factory=list)

    # Inter-agent communication & A2A protocol tracking
    agent_messages: List[AgentMessage] = Field(default_factory=list)
    a2a_tasks: List[A2ATaskRecord] = Field(default_factory=list)

    # MCP Tool execution log
    tool_calls: List[ToolCallRecord] = Field(default_factory=list)

    # File tracking
    generated_files: List[str] = Field(default_factory=list)
    modified_files: List[str] = Field(default_factory=list)

    # Validation, Testing, & Security
    test_results: TestRunMetrics = Field(default_factory=TestRunMetrics)
    security_findings: List[SecurityScanFinding] = Field(default_factory=list)
    review_result: ReviewMetricScore = Field(default_factory=ReviewMetricScore)
    validation_errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)

    # Human-in-the-loop approval
    human_approval_required: bool = False
    human_approval_action: str = ""
    human_approval_granted: Optional[bool] = None

    # Telemetry and Execution Metrics
    total_tokens_used: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    estimated_cost_usd: float = 0.0
    stage_latencies_ms: Dict[str, float] = Field(default_factory=dict)

    def record_stage_latency(self, stage: str, duration_ms: float) -> None:
        self.stage_latencies_ms[stage] = round(duration_ms, 2)
        self.updated_at = utc_now_iso()

    def record_tool_call(self, record: ToolCallRecord) -> None:
        self.tool_calls.append(record)
        self.updated_at = utc_now_iso()

    def record_a2a_task(self, record: A2ATaskRecord) -> None:
        self.a2a_tasks.append(record)
        self.updated_at = utc_now_iso()

    def record_tokens(self, prompt: int, completion: int, cost: float = 0.0) -> None:
        self.prompt_tokens += prompt
        self.completion_tokens += completion
        self.total_tokens_used += (prompt + completion)
        if cost > 0.0:
            self.estimated_cost_usd += cost
        else:
            self.estimated_cost_usd += (prompt / 1000.0 * 0.00020) + (completion / 1000.0 * 0.00080)
        self.updated_at = utc_now_iso()
