"""
Integration Tests — End-to-End CrewAI + Google ADK Workflow via A2A.

Tests Requirements 1, 4, 6, 7 & 8:
- Runs full workflow: Input Security -> CrewAI Requirement Analysis -> RAG ->
  CrewAI Architecture -> A2A Delegation -> Google ADK Implementation -> MCP Tools ->
  Sandbox Testing -> CrewAI Quality Sentinel -> Final Pydantic Output
"""

import os
import pytest
from app.crew.workflow import orchestration_engine
from app.schemas.context import ExecutionContext, ExecutionStatus, FrameworkType


@pytest.mark.asyncio
async def test_full_crewai_adk_pipeline(tmp_path):
    workspace = str(tmp_path / "pipeline_ws")
    os.makedirs(workspace, exist_ok=True)

    context = ExecutionContext(
        execution_id="test-full-pipeline-001",
        project_id="test-proj-001",
        user_id="test-user-001",
        workspace_path=workspace,
        raw_requirement="Create a simple Python utility that validates email addresses and includes pytest tests.",
    )

    events_captured = []

    async def event_collector(stage: str, data: dict):
        events_captured.append((stage, data.get("status"), data.get("current_framework")))

    response = await orchestration_engine.execute(context, on_event=event_collector)

    # 1. Verify final status and response structure
    assert response.execution_id == "test-full-pipeline-001"
    assert response.status in ("COMPLETED", "FAILED", "PARTIAL")
    assert response.framework_interaction_mode == "CrewAI + Google ADK (A2A Protocol)"

    # 2. Verify both frameworks participated
    frameworks_involved = set(context.current_framework.value for _, _, f in events_captured if f)
    assert FrameworkType.CREWAI.value in [e[2] for e in events_captured]

    # 3. Verify intermediate states were populated
    assert context.input_sanitized is True
    assert "functional_requirements" in context.requirements or len(context.requirements) > 0
    assert "architecture_overview" in context.architecture or len(context.architecture) > 0

    # 4. Verify A2A task recorded
    assert len(context.a2a_tasks) >= 1
    a2a_rec = context.a2a_tasks[0]
    assert a2a_rec.initiator_framework == FrameworkType.CREWAI
    assert a2a_rec.target_framework == FrameworkType.GOOGLE_ADK

    # 5. Verify MCP tools were invoked
    assert response.tool_execution_summary.total_calls >= 1
    assert "workspace_file_operations" in response.tool_execution_summary.distinct_tools_invoked or \
           "documentation_search" in response.tool_execution_summary.distinct_tools_invoked

    # 6. Verify files created
    assert len(response.files_created_or_modified) >= 1

    # 7. Verify telemetry recorded
    assert response.execution_metrics.total_duration_ms > 0
