"""
DevCrew Structured Final Output Schemas — Pydantic Validated.

Satisfies Requirement 3:
- Explicit Pydantic schemas for final response and agent artifacts
- Schema validation with controlled error handling & repair attempts
- Structured summary suitable for UI rendering (markdown, tables, metric cards)
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class ToolExecutionSummary(BaseModel):
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    distinct_tools_invoked: List[str] = Field(default_factory=list)
    call_details: List[Dict[str, Any]] = Field(default_factory=list)


class SourceReferenceSummary(BaseModel):
    title: str
    source_type: str
    relevance_snippet: str
    url_or_path: Optional[str] = None


class TestResultsSummary(BaseModel):
    tests_passed: bool = False
    total_tests: int = 0
    passed_tests: int = 0
    failed_tests: int = 0
    coverage_percentage: float = 0.0
    failure_details: List[str] = Field(default_factory=list)


class ExecutionMetricsSummary(BaseModel):
    total_duration_ms: float = 0.0
    total_tokens_used: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    estimated_cost_usd: float = 0.0
    stage_durations: Dict[str, float] = Field(default_factory=dict)
    framework_breakdown: Dict[str, str] = Field(
        default_factory=lambda: {
            "requirements": "CrewAI (Requirement Analyst Agent)",
            "architecture": "CrewAI (Software Architect Agent)",
            "planning": "CrewAI (Manager & Task Planner)",
            "implementation": "Google ADK (Developer Agent via A2A Protocol)",
            "tools": "Model Context Protocol (FastMCP)",
            "testing": "Google ADK / Pytest Sandbox",
            "security_review": "CrewAI (Sentinel & Code Reviewer)",
        }
    )


class FinalExecutionResponse(BaseModel):
    """
    Validated Structured Final Response for DevCrew project execution.
    """
    execution_id: str
    project_id: str
    status: str
    framework_interaction_mode: str = "CrewAI + Google ADK (A2A Protocol)"
    requirement_summary: str
    architecture_summary: str
    implementation_summary: str
    files_created_or_modified: List[str] = Field(default_factory=list)
    tool_execution_summary: ToolExecutionSummary = Field(default_factory=ToolExecutionSummary)
    retrieved_sources: List[SourceReferenceSummary] = Field(default_factory=list)
    test_results: TestResultsSummary = Field(default_factory=TestResultsSummary)
    security_summary: Dict[str, Any] = Field(default_factory=dict)
    review_summary: Dict[str, Any] = Field(default_factory=dict)
    validation_errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    execution_metrics: ExecutionMetricsSummary = Field(default_factory=ExecutionMetricsSummary)

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        valid_statuses = {"COMPLETED", "FAILED", "PAUSED", "WAITING_FOR_APPROVAL", "PARTIAL"}
        if v.upper() not in valid_statuses:
            return "COMPLETED" if "pass" in v.lower() or "success" in v.lower() else "FAILED"
        return v.upper()

    def to_markdown_summary(self) -> str:
        """Render the structured output as human-readable Markdown for reports & UI."""
        md = []
        md.append(f"# DevCrew Execution Report — `{self.execution_id}`\n")
        md.append(f"**Status:** `{self.status}` | **Architecture Mode:** {self.framework_interaction_mode}\n")
        md.append(f"## 📋 Requirement Analysis\n{self.requirement_summary}\n")
        md.append(f"## 🏛️ System Architecture\n{self.architecture_summary}\n")
        md.append(f"## 💻 Implementation (Google ADK via A2A)\n{self.implementation_summary}\n")
        
        md.append("### Files Created or Modified\n")
        if self.files_created_or_modified:
            for f in self.files_created_or_modified:
                md.append(f"- `{f}`")
        else:
            md.append("*No files modified*")
        md.append("")

        md.append("## 🧪 Testing & Quality\n")
        md.append(f"- **Tests Passed:** {'✅ Yes' if self.test_results.tests_passed else '❌ No'}")
        md.append(f"- **Total Tests:** {self.test_results.total_tests} (Passed: {self.test_results.passed_tests}, Failed: {self.test_results.failed_tests})")
        md.append(f"- **Code Coverage:** {self.test_results.coverage_percentage:.1f}%\n")

        md.append("## 🛠️ MCP Tool Execution\n")
        md.append(f"- **Total Calls:** {self.tool_execution_summary.total_calls}")
        md.append(f"- **Distinct Tools:** {', '.join(self.tool_execution_summary.distinct_tools_invoked) or 'None'}\n")

        md.append("## 📊 Execution Metrics & Telemetry\n")
        md.append(f"- **Duration:** {self.execution_metrics.total_duration_ms / 1000:.2f}s")
        md.append(f"- **Tokens Used:** {self.execution_metrics.total_tokens_used:,}")
        md.append(f"- **Estimated Cost:** ${self.execution_metrics.estimated_cost_usd:.4f}\n")

        if self.warnings:
            md.append("### ⚠️ Warnings\n")
            for w in self.warnings:
                md.append(f"- {w}")

        return "\n".join(md)
