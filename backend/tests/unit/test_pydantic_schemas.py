"""
Unit Tests — Pydantic Context and Structured Output Schemas.

Tests Requirements 1 & 3:
- ExecutionContext typed model validation
- FinalExecutionResponse serialization and markdown conversion
- AgentCard and A2A schemas
"""

import pytest
from app.schemas.context import (
    ExecutionContext,
    ExecutionStatus,
    FrameworkType,
    ToolCallRecord,
)
from app.schemas.output import (
    FinalExecutionResponse,
    TestResultsSummary,
    ToolExecutionSummary,
)
from app.a2a.models import AgentCard, A2ATaskSubmitRequest


def test_execution_context_defaults():
    ctx = ExecutionContext(
        execution_id="exec-123",
        project_id="proj-456",
        user_id="user-789",
        workspace_path="/app/workspaces/test",
        raw_requirement="Build a task tracker API",
    )
    assert ctx.status == ExecutionStatus.INITIALIZED
    assert ctx.current_framework == FrameworkType.CREWAI
    assert ctx.tool_calls == []
    assert ctx.a2a_tasks == []


def test_execution_context_record_tool_call():
    ctx = ExecutionContext(
        execution_id="exec-123",
        project_id="proj-456",
        user_id="user-789",
        workspace_path="/app/workspaces/test",
        raw_requirement="Build a task tracker API",
    )
    record = ToolCallRecord(
        tool_name="workspace_file_operations",
        arguments={"action": "write_file", "file_path": "main.py"},
        result_summary="File written successfully",
        success=True,
        duration_ms=15.2,
    )
    ctx.record_tool_call(record)
    assert len(ctx.tool_calls) == 1
    assert ctx.tool_calls[0].tool_name == "workspace_file_operations"


def test_final_execution_response_markdown():
    resp = FinalExecutionResponse(
        execution_id="exec-999",
        project_id="proj-999",
        status="COMPLETED",
        requirement_summary="Requirement for task tracker API",
        architecture_summary="FastAPI layered architecture with SQLite database",
        implementation_summary="Generated 3 files via Google ADK through A2A",
        files_created_or_modified=["app/main.py", "app/models.py", "tests/test_main.py"],
        tool_execution_summary=ToolExecutionSummary(
            total_calls=4,
            successful_calls=4,
            failed_calls=0,
            distinct_tools_invoked=["workspace_file_operations", "documentation_search"],
        ),
        test_results=TestResultsSummary(
            tests_passed=True,
            total_tests=5,
            passed_tests=5,
            failed_tests=0,
            coverage_percentage=85.0,
        ),
    )
    md = resp.to_markdown_summary()
    assert "# DevCrew Execution Report" in md
    assert "exec-999" in md
    assert "CrewAI + Google ADK" in md
    assert "workspace_file_operations" in md
    assert "85.0%" in md
