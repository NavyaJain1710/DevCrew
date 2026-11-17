"""Reports API — test results, security findings, review results, artifact download."""

from __future__ import annotations

import os
import re
import uuid
import zipfile
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

from app.dependencies import CurrentUser, DBSession

router = APIRouter(prefix="/projects", tags=["Reports"])


def _generate_project_report_md(project) -> str:
    """Generate a clean, professional markdown project report."""
    created_str = project.created_at.strftime("%Y-%m-%d %H:%M:%S UTC") if project.created_at else "N/A"
    completed_str = project.completed_at.strftime("%Y-%m-%d %H:%M:%S UTC") if project.completed_at else "In Progress"

    sections = [
        f"# DevCrew Project Execution Report: {project.name}",
        f"\n**Generated on:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}",
        f"**Project ID:** `{project.id}`",
        f"**Status:** `{project.status.value if hasattr(project.status, 'value') else project.status}`",
        f"**Created:** {created_str} | **Completed:** {completed_str}",
        f"**Total Iterations:** {project.iteration_count or 1}",
        f"**Estimated LLM Cost:** ${(project.estimated_cost_usd or 0.0):.4f}",
        "\n---",
        "\n## 1. Requirement Specification",
        f"\n**Raw Input Requirement:**\n> {project.raw_requirement or 'No input requirement provided.'}",
    ]

    # Requirements Breakdown
    if project.requirements:
        req = project.requirements[-1].structured_data or {}
        if isinstance(req, dict):
            features = req.get("functional_requirements") or req.get("features") or []
            if features:
                sections.append("\n### Functional Requirements")
                for f in features:
                    if isinstance(f, dict):
                        sections.append(f"- **{f.get('title', 'Requirement')}**: {f.get('description', '')}")
                    else:
                        sections.append(f"- {f}")

    # Architecture Overview
    if project.architectures:
        arch = project.architectures[-1].system_design or {}
        if isinstance(arch, dict):
            sections.append("\n## 2. Technical Architecture")
            overview = arch.get("architecture_overview") or arch.get("overview")
            if overview:
                sections.append(f"\n{overview}\n")
            tech_stack = arch.get("tech_stack") or []
            if tech_stack:
                sections.append(f"**Technology Stack:** {', '.join(tech_stack) if isinstance(tech_stack, list) else str(tech_stack)}")

    # Test Results
    if project.test_runs:
        last_test = project.test_runs[-1]
        sections.append("\n## 3. Automated Sandbox Test Results")
        sections.append(f"- **Overall Status:** `{last_test.overall_status}`")
        sections.append(f"- **Tests Passed:** {last_test.passed}")
        sections.append(f"- **Tests Failed:** {last_test.failed}")
        sections.append(f"- **Execution Time:** {last_test.execution_time_ms} ms")
        if last_test.coverage_percent is not None:
            sections.append(f"- **Code Coverage:** {last_test.coverage_percent}%")

    # Security Scan
    if project.security_scans:
        scan = project.security_scans[-1]
        sections.append("\n## 4. Security & Vulnerability Analysis")
        sections.append(f"- **Status:** `{scan.status}`")
        sections.append(f"- **Critical:** {scan.critical_count} | **High:** {scan.high_count} | **Medium:** {scan.medium_count} | **Low:** {scan.low_count}")
        if scan.findings and isinstance(scan.findings, list):
            sections.append("\n### Key Findings:")
            for item in scan.findings[:5]:
                if isinstance(item, dict):
                    sections.append(f"- **[{item.get('severity', 'INFO')}]** {item.get('title', 'Notice')}: {item.get('description', '')}")

    # Review Results
    if getattr(project, "review_results", None):
        review = project.review_results[-1]
        sections.append("\n## 5. Code Review & Quality Assessment")
        sections.append(f"- **Overall Quality Score:** {review.overall_score}/10")
        sections.append(f"- **Code Quality:** {review.code_quality_score}/10 | **Architecture:** {review.architecture_score}/10 | **Security:** {review.security_score}/10 | **Testing:** {review.testing_score}/10")
        if review.strengths and isinstance(review.strengths, list):
            sections.append("\n**Key Strengths:**")
            for s in review.strengths:
                sections.append(f"- {s}")
        if review.recommendations and isinstance(review.recommendations, list):
            sections.append("\n**Recommendations:**")
            for r in review.recommendations:
                sections.append(f"- {r}")

    # Generated files
    if project.workspace_path and os.path.exists(project.workspace_path):
        ignore_dirs = {".git", "__pycache__", ".pytest_cache", ".venv", "venv", "node_modules", ".devcrew_artifacts"}
        file_tree = []
        for root, dirs, files in os.walk(project.workspace_path):
            dirs[:] = [d for d in dirs if d not in ignore_dirs and not d.startswith(".")]
            for file in sorted(files):
                if not file.endswith((".pyc", ".pyo")):
                    rel = os.path.relpath(os.path.join(root, file), project.workspace_path)
                    file_tree.append(f"- `{rel}`")
        if file_tree:
            sections.append(f"\n## 6. Generated Project Files ({len(file_tree)} total)")
            sections.extend(file_tree)

    sections.append("\n\n---\n*Report automatically generated by DevCrew Autonomous Agentic Platform.*")
    return "\n".join(sections)


@router.get("/{project_id}/tests")
async def get_test_results(
    project_id: uuid.UUID,
    current_user: CurrentUser,
    db: DBSession,
):
    from app.database.models import TestRun
    from app.database.repositories.projects import ProjectRepository
    from sqlalchemy import select

    repo = ProjectRepository(db)
    project = await repo.get_by_id(project_id)
    if not project or str(project.user_id) != str(current_user.id):
        raise HTTPException(status_code=404, detail="Project not found.")

    result = await db.execute(
        select(TestRun)
        .where(TestRun.project_id == project_id)
        .order_by(TestRun.created_at.desc())
    )
    runs = result.scalars().all()
    return [
        {
            "id": str(r.id),
            "iteration": r.iteration,
            "overall_status": r.overall_status,
            "passed": r.passed,
            "failed": r.failed,
            "skipped": r.skipped,
            "coverage_percent": r.coverage_percent,
            "execution_time_ms": r.execution_time_ms,
            "failures": r.failures,
            "recommendations": r.recommendations,
            "timestamp": r.created_at.isoformat(),
        }
        for r in runs
    ]


@router.get("/{project_id}/security")
async def get_security_results(
    project_id: uuid.UUID,
    current_user: CurrentUser,
    db: DBSession,
):
    from app.database.models import SecurityScan
    from app.database.repositories.projects import ProjectRepository
    from sqlalchemy import select

    repo = ProjectRepository(db)
    project = await repo.get_by_id(project_id)
    if not project or str(project.user_id) != str(current_user.id):
        raise HTTPException(status_code=404, detail="Project not found.")

    result = await db.execute(
        select(SecurityScan)
        .where(SecurityScan.project_id == project_id)
        .order_by(SecurityScan.created_at.desc())
        .limit(1)
    )
    scan = result.scalar_one_or_none()
    if not scan:
        return {"status": "not_run", "findings": []}

    return {
        "id": str(scan.id),
        "scanner": scan.scanner,
        "critical_count": scan.critical_count,
        "high_count": scan.high_count,
        "medium_count": scan.medium_count,
        "low_count": scan.low_count,
        "findings": scan.findings,
        "status": scan.status,
        "timestamp": scan.created_at.isoformat(),
    }


@router.get("/{project_id}/review")
async def get_review_results(
    project_id: uuid.UUID,
    current_user: CurrentUser,
    db: DBSession,
):
    from app.database.models import ReviewResult
    from app.database.repositories.projects import ProjectRepository
    from sqlalchemy import select

    repo = ProjectRepository(db)
    project = await repo.get_by_id(project_id)
    if not project or str(project.user_id) != str(current_user.id):
        raise HTTPException(status_code=404, detail="Project not found.")

    result = await db.execute(
        select(ReviewResult)
        .where(ReviewResult.project_id == project_id)
        .order_by(ReviewResult.created_at.desc())
        .limit(1)
    )
    review = result.scalar_one_or_none()
    if not review:
        return {"status": "not_run"}

    return {
        "id": str(review.id),
        "status": review.status,
        "overall_score": review.overall_score,
        "code_quality_score": review.code_quality_score,
        "architecture_score": review.architecture_score,
        "security_score": review.security_score,
        "testing_score": review.testing_score,
        "documentation_score": review.documentation_score,
        "strengths": review.strengths,
        "issues": review.issues,
        "recommendations": review.recommendations,
        "timestamp": review.created_at.isoformat(),
    }


@router.get("/{project_id}/reports/download")
async def download_project_artifact(
    project_id: uuid.UUID,
    current_user: CurrentUser,
    db: DBSession,
    type: str = Query("zip", description="Artifact type to download: 'zip' or 'report'"),
):
    """Download the generated project as a ZIP archive or Markdown report."""
    from app.database.models import ProjectArtifact
    from app.database.repositories.projects import ProjectRepository
    from sqlalchemy import select

    repo = ProjectRepository(db)
    project = await repo.get_by_id(project_id, load_relations=True)
    if not project or str(project.user_id) != str(current_user.id):
        raise HTTPException(status_code=404, detail="Project not found.")

    clean_name = re.sub(r'[^a-zA-Z0-9_\-]', '_', project.name).strip('_') or f"project_{project_id}"

    # Handle Report Download
    if type == "report":
        res = await db.execute(
            select(ProjectArtifact)
            .where(
                ProjectArtifact.project_id == project_id,
                ProjectArtifact.artifact_type == "report",
            )
            .order_by(ProjectArtifact.created_at.desc())
            .limit(1)
        )
        artifact = res.scalar_one_or_none()
        if artifact and os.path.exists(artifact.file_path):
            return FileResponse(
                path=artifact.file_path,
                filename=f"{clean_name}_report.md",
                media_type="text/markdown",
            )

        report_content = _generate_project_report_md(project)
        artifacts_dir = os.path.join(project.workspace_path or f"/app/workspaces/{project_id}", ".devcrew_artifacts")
        os.makedirs(artifacts_dir, exist_ok=True)
        report_path = os.path.join(artifacts_dir, "project-report.md")
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report_content)

        new_artifact = ProjectArtifact(
            project_id=project_id,
            artifact_type="report",
            file_path=report_path,
            file_size_bytes=os.path.getsize(report_path),
        )
        db.add(new_artifact)
        await db.commit()

        return FileResponse(
            path=report_path,
            filename=f"{clean_name}_report.md",
            media_type="text/markdown",
        )

    # Handle ZIP Archive Download
    workspace = project.workspace_path or f"/app/workspaces/{project_id}"
    if not os.path.exists(workspace):
        raise HTTPException(
            status_code=404,
            detail="No files found in workspace. Run the pipeline first to generate code.",
        )

    # Automatically ensure workspace has run.py, start.bat, start.sh, uvicorn, and README
    try:
        from app.services.workspace_prep import ensure_workspace_runnable
        ensure_workspace_runnable(workspace, project.name, project.raw_requirement or "")
    except Exception as e:
        pass

    artifacts_dir = os.path.join(workspace, ".devcrew_artifacts")
    os.makedirs(artifacts_dir, exist_ok=True)
    zip_path = os.path.join(artifacts_dir, f"project-{project_id}.zip")

    ignore_dirs = {".git", "__pycache__", ".pytest_cache", ".venv", "venv", "node_modules", ".devcrew_artifacts"}
    files_added = 0
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(workspace):
            dirs[:] = [d for d in dirs if d not in ignore_dirs and not d.startswith(".")]
            for file in sorted(files):
                if file.endswith((".pyc", ".pyo")):
                    continue
                file_abs = os.path.join(root, file)
                rel_path = os.path.relpath(file_abs, workspace)
                zipf.write(file_abs, arcname=rel_path)
                files_added += 1

    if files_added == 0:
        if os.path.exists(zip_path):
            os.remove(zip_path)
        raise HTTPException(
            status_code=404,
            detail="No files found in workspace. Run the pipeline first to generate code.",
        )

    # Upsert or update ProjectArtifact
    res = await db.execute(
        select(ProjectArtifact)
        .where(
            ProjectArtifact.project_id == project_id,
            ProjectArtifact.artifact_type == "zip",
        )
        .order_by(ProjectArtifact.created_at.desc())
        .limit(1)
    )
    artifact = res.scalar_one_or_none()
    if not artifact:
        artifact = ProjectArtifact(
            project_id=project_id,
            artifact_type="zip",
            file_path=zip_path,
            file_size_bytes=os.path.getsize(zip_path),
        )
        db.add(artifact)
    else:
        artifact.file_path = zip_path
        artifact.file_size_bytes = os.path.getsize(zip_path)
    await db.commit()

    return FileResponse(
        path=zip_path,
        filename=f"{clean_name}.zip",
        media_type="application/zip",
    )
