"""
DevCrew Orchestrator Service — Multi-Agent Coordinator using CrewAI and Google ADK.

Satisfies Requirements 1, 4, 5, 6, 7 & 8:
- Rips out LangGraph entirely; powered by 100% CrewAI and Google ADK via A2A
- Persists all intermediate and final state models to PostgreSQL
- Broadcasts real-time events and framework milestones via WebSocket
"""

from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional
import structlog

from app.config import get_settings
from app.crew.workflow import orchestration_engine
from app.database.base import AsyncSessionLocal
from app.database.models import (
    AgentTask,
    Architecture,
    ProjectRequirement,
    ProjectStatus,
    ReviewResult,
    SecurityScan,
    TestRun,
)
from app.database.repositories.projects import ProjectRepository
from app.schemas.context import ExecutionContext, ExecutionStatus
from app.services.ws_hub import ws_hub

logger = structlog.get_logger(__name__)
settings = get_settings()


class DevCrewOrchestrator:
    """
    Production orchestrator coordinating CrewAI and Google ADK via A2A.
    """

    def __init__(self) -> None:
        self._engine = orchestration_engine

    async def run(self, project_id: str, user_id: str) -> None:
        """
        Execute the end-to-end multi-agent pipeline for a project.
        Called asynchronously in background task.
        """
        logger.info("devcrew_orchestrator_start", project_id=project_id, user_id=user_id)

        # 1. Fetch project from database
        async with AsyncSessionLocal() as db:
            repo = ProjectRepository(db)
            project = await repo.get_by_id(uuid.UUID(project_id))
            if not project:
                logger.error("orchestrator_project_not_found", project_id=project_id)
                return

            workspace_path = os.path.join(settings.workspace_base_path, project_id)
            os.makedirs(workspace_path, exist_ok=True)
            await repo.update_workspace(project.id, workspace_path)
            await repo.update_status(project.id, ProjectStatus.ANALYZING)
            await db.commit()
            raw_req = project.raw_requirement

        # 2. Build Typed Shared Execution Context
        context = ExecutionContext(
            execution_id=f"exec-{uuid.uuid4().hex[:12]}",
            project_id=project_id,
            user_id=user_id,
            workspace_path=workspace_path,
            raw_requirement=raw_req,
            max_iterations=settings.max_iterations_per_project,
        )

        # 3. Define event callback for database persistence & WebSocket broadcasts
        async def handle_pipeline_event(stage: str, event_data: Dict[str, Any]) -> None:
            await self._persist_stage_to_db(project_id, stage, event_data, context)

        # 4. Execute the multi-agent pipeline
        try:
            final_response = await self._engine.execute(context, on_event=handle_pipeline_event)

            # 5. Final DB sync & status completion
            async with AsyncSessionLocal() as db:
                repo = ProjectRepository(db)
                proj = await repo.get_by_id(uuid.UUID(project_id), load_relations=True)
                if proj:
                    final_status = (
                        ProjectStatus.COMPLETED
                        if final_response.status in ("COMPLETED", "PARTIAL")
                        else ProjectStatus.FAILED
                    )
                    proj.status = final_status
                    proj.completed_at = datetime.now(timezone.utc)
                    proj.error_message = None if final_status == ProjectStatus.COMPLETED else "; ".join(final_response.validation_errors)
                    proj.total_prompt_tokens = final_response.execution_metrics.prompt_tokens or context.prompt_tokens
                    proj.total_completion_tokens = final_response.execution_metrics.completion_tokens or context.completion_tokens
                    proj.estimated_cost_usd = final_response.execution_metrics.estimated_cost_usd or context.estimated_cost_usd

                    # Persist ModelUsage record for reporting and telemetry
                    from app.database.models import ModelUsage
                    p_tok = proj.total_prompt_tokens
                    c_tok = proj.total_completion_tokens
                    cost_val = proj.estimated_cost_usd
                    if p_tok > 0 or c_tok > 0:
                        db.add(
                            ModelUsage(
                                project_id=proj.id,
                                agent="DevCrew Multi-Agent Team",
                                model=settings.coding_model,
                                provider=settings.coding_provider,
                                task_type="FULL_PIPELINE",
                                prompt_tokens=p_tok,
                                completion_tokens=c_tok,
                                latency_ms=int(final_response.execution_metrics.total_duration_ms),
                                estimated_cost_usd=cost_val,
                                success=(final_status == ProjectStatus.COMPLETED),
                            )
                        )
                    await db.commit()

                    # Automatically index generated workspace files into Dynamic RAG ChromaDB
                    if proj.workspace_path and os.path.exists(proj.workspace_path):
                        try:
                            from app.rag.service import rag_service
                            rag_service.index_workspace(
                                workspace_path=proj.workspace_path,
                                user_id=str(proj.user_id),
                                project_id=str(proj.id),
                            )
                            logger.info("auto_workspace_rag_indexed", project_id=str(proj.id))
                        except Exception as err:
                            logger.warning("auto_rag_index_failed", error=str(err))

                        # Pre-generate ZIP package and project artifact records
                        try:
                            from app.services.workspace_prep import ensure_workspace_runnable
                            ensure_workspace_runnable(proj.workspace_path, proj.name, proj.raw_requirement or "")
                        except Exception as prep_err:
                            logger.warning("auto_prep_workspace_failed", error=str(prep_err))

                        try:
                            import zipfile
                            from app.database.models import ProjectArtifact
                            artifacts_dir = os.path.join(proj.workspace_path, ".devcrew_artifacts")
                            os.makedirs(artifacts_dir, exist_ok=True)
                            zip_path = os.path.join(artifacts_dir, f"project-{proj.id}.zip")
                            ignore_dirs = {".git", "__pycache__", ".pytest_cache", ".venv", "venv", "node_modules", ".devcrew_artifacts"}
                            file_count = 0
                            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                                for root, dirs, files in os.walk(proj.workspace_path):
                                    dirs[:] = [d for d in dirs if d not in ignore_dirs and not d.startswith(".")]
                                    for f in files:
                                        if not f.endswith((".pyc", ".pyo")):
                                            fp = os.path.join(root, f)
                                            zipf.write(fp, arcname=os.path.relpath(fp, proj.workspace_path))
                                            file_count += 1
                            if file_count > 0:
                                artifact = ProjectArtifact(
                                    project_id=proj.id,
                                    artifact_type="zip",
                                    file_path=zip_path,
                                    file_size_bytes=os.path.getsize(zip_path),
                                )
                                db.add(artifact)
                                await db.commit()
                                logger.info("auto_zip_artifact_created", project_id=str(proj.id), files=file_count)
                        except Exception as err:
                            logger.warning("auto_zip_artifact_failed", error=str(err))

            await ws_hub.broadcast(
                project_id,
                "project_completed",
                {
                    "project_id": project_id,
                    "status": final_response.status,
                    "metrics": final_response.execution_metrics.model_dump(),
                    "files_created": final_response.files_created_or_modified,
                },
            )
            logger.info("devcrew_orchestrator_complete", project_id=project_id, status=final_response.status)

        except Exception as e:
            logger.error("orchestrator_fatal_error", project_id=project_id, error=str(e))
            async with AsyncSessionLocal() as db:
                repo = ProjectRepository(db)
                proj = await repo.get_by_id(uuid.UUID(project_id))
                if proj:
                    proj.status = ProjectStatus.FAILED
                    proj.error_message = str(e)
                    if context.prompt_tokens > 0:
                        proj.total_prompt_tokens = context.prompt_tokens
                    if context.completion_tokens > 0:
                        proj.total_completion_tokens = context.completion_tokens
                    if context.estimated_cost_usd > 0:
                        proj.estimated_cost_usd = context.estimated_cost_usd
                await db.commit()
            await ws_hub.broadcast(project_id, "error", {"project_id": project_id, "error": str(e)})

    async def _persist_stage_to_db(
        self,
        project_id: str,
        stage: str,
        data: Dict[str, Any],
        context: ExecutionContext,
    ) -> None:
        """Persist intermediate agent artifacts into relational PostgreSQL tables."""
        try:
            async with AsyncSessionLocal() as db:
                repo = ProjectRepository(db)
                project = await repo.get_by_id(uuid.UUID(project_id), load_relations=True)
                if not project:
                    return

                # Map stage to ProjectStatus enum
                status_mapping = {
                    "requirement_analysis": ProjectStatus.ANALYZING,
                    "architecture_design": ProjectStatus.ARCHITECTING,
                    "a2a_delegation": ProjectStatus.IMPLEMENTING,
                    "implementation": ProjectStatus.IMPLEMENTING,
                    "security_review": ProjectStatus.REVIEWING,
                }
                if stage in status_mapping:
                    project.status = status_mapping[stage]

                # Update live tokens and estimated cost in database
                from app.observability.tracer import observability
                trace_summary = observability.get_summary(context.execution_id)
                cur_p = trace_summary.get("prompt_tokens") or context.prompt_tokens
                cur_c = trace_summary.get("completion_tokens") or context.completion_tokens
                cur_cost = trace_summary.get("estimated_cost_usd") or context.estimated_cost_usd
                if cur_p > 0:
                    project.total_prompt_tokens = cur_p
                if cur_c > 0:
                    project.total_completion_tokens = cur_c
                if cur_cost > 0:
                    project.estimated_cost_usd = cur_cost

                # Requirements
                if context.requirements:
                    if not project.requirements:
                        project.requirements.append(ProjectRequirement(structured_data=context.requirements, version=1))
                    else:
                        project.requirements[-1].structured_data = context.requirements

                # Architecture
                if context.architecture:
                    if not project.architectures:
                        project.architectures.append(Architecture(system_design=context.architecture, version=1))
                    else:
                        project.architectures[-1].system_design = context.architecture

                # Test Runs
                if context.test_results.total > 0:
                    failures_data = [f.model_dump() for f in context.test_results.failures]
                    if not project.test_runs:
                        project.test_runs.append(
                            TestRun(
                                overall_status="passed" if context.test_results.tests_passed else "failed",
                                passed=context.test_results.passed,
                                failed=context.test_results.failed,
                                coverage_percent=context.test_results.coverage_percent,
                                failures=failures_data,
                            )
                        )
                    else:
                        tr = project.test_runs[-1]
                        tr.overall_status = "passed" if context.test_results.tests_passed else "failed"
                        tr.passed = context.test_results.passed
                        tr.failed = context.test_results.failed
                        tr.coverage_percent = context.test_results.coverage_percent
                        tr.failures = failures_data

                # Security Scans
                if context.security_findings:
                    findings_data = [f.model_dump() for f in context.security_findings]
                    if not project.security_scans:
                        project.security_scans.append(
                            SecurityScan(
                                scanner="DevCrew Quality Sentinel (CrewAI)",
                                critical_count=sum(1 for f in context.security_findings if f.severity == "critical"),
                                high_count=sum(1 for f in context.security_findings if f.severity == "high"),
                                findings=findings_data,
                                status="completed",
                            )
                        )

                # Review Result
                if context.review_result.overall_score > 0:
                    rr = context.review_result
                    if not project.review_results:
                        project.review_results.append(
                            ReviewResult(
                                status="approved" if rr.approved else "rejected",
                                overall_score=rr.overall_score,
                                code_quality_score=rr.code_quality_score,
                                architecture_score=rr.architecture_score,
                                security_score=rr.security_score,
                                testing_score=rr.testing_score,
                                documentation_score=rr.documentation_score,
                                strengths=rr.strengths,
                                issues=rr.issues,
                                recommendations=rr.recommendations,
                            )
                        )

                # Agent Tasks tracking
                # Record CrewAI and Google ADK tasks for the Agents UI tab
                from app.database.models import AgentName, TaskStatus

                tasks_to_record = [
                    (AgentName.REQUIREMENT, "Requirement Analysis (CrewAI)", context.requirements),
                    (AgentName.ARCHITECT, "System Architecture Design (CrewAI)", context.architecture),
                    (AgentName.DEVELOPER, "Code Implementation & Testing (Google ADK via A2A)", {"files": context.generated_files}),
                    (AgentName.SECURITY, "Quality & Security Sentinel (CrewAI)", context.review_result.model_dump()),
                ]
                project.tasks.clear()
                for idx, (agent_enum, obj, out_data) in enumerate(tasks_to_record, start=1):
                    if out_data:
                        project.tasks.append(
                            AgentTask(
                                agent=agent_enum,
                                status=TaskStatus.COMPLETED,
                                objective=obj,
                                input_data={"raw_requirement": context.raw_requirement},
                                output_data={"data": out_data},
                                iteration=1,
                            )
                        )

                await db.commit()

                # Automatically index generated workspace files into Dynamic RAG ChromaDB
                if stage in ("completed", "security_review") and project.workspace_path and os.path.exists(project.workspace_path):
                    try:
                        from app.rag.service import rag_service
                        rag_service.index_workspace(
                            workspace_path=project.workspace_path,
                            user_id=str(project.user_id),
                            project_id=str(project.id),
                        )
                        logger.info("auto_workspace_rag_indexed", project_id=str(project.id))
                    except Exception as err:
                        logger.warning("auto_rag_index_failed", error=str(err))

        except Exception as ex:
            logger.error("failed_persisting_stage_db", stage=stage, error=str(ex))
