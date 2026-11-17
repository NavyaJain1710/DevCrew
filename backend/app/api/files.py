"""Files API — browse and read generated project files."""

from __future__ import annotations

import os
import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.dependencies import CurrentUser, DBSession
from app.tools.filesystem import FileSystemTools

router = APIRouter(prefix="/projects", tags=["Files"])
fs = FileSystemTools()


class FileListResponse(BaseModel):
    files: list[str]
    workspace_path: str


class FileContentResponse(BaseModel):
    path: str
    content: str
    size_bytes: int
    language: str


class FileChangeResponse(BaseModel):
    file_path: str
    change_type: str
    before_content: str | None
    after_content: str | None
    reason: str | None
    agent: str | None
    timestamp: str


def _detect_language(filename: str) -> str:
    ext_map = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".tsx": "typescriptreact",
        ".jsx": "javascriptreact",
        ".html": "html",
        ".css": "css",
        ".json": "json",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".md": "markdown",
        ".sql": "sql",
        ".sh": "bash",
        ".dockerfile": "dockerfile",
        ".toml": "toml",
        ".env": "plaintext",
    }
    _, ext = os.path.splitext(filename.lower())
    if "dockerfile" in filename.lower():
        return "dockerfile"
    return ext_map.get(ext, "plaintext")


@router.get("/{project_id}/files", response_model=FileListResponse)
async def list_files(
    project_id: uuid.UUID,
    current_user: CurrentUser,
    db: DBSession,
):
    from app.database.repositories.projects import ProjectRepository

    repo = ProjectRepository(db)
    project = await repo.get_by_id(project_id)
    if not project or str(project.user_id) != str(current_user.id):
        raise HTTPException(status_code=404, detail="Project not found.")

    workspace = project.workspace_path or f"/app/workspaces/{project_id}"
    if not os.path.exists(workspace):
        return FileListResponse(files=[], workspace_path=workspace)

    ignore_dirs = {".git", "__pycache__", ".pytest_cache", ".venv", "venv", "node_modules", ".devcrew_artifacts"}
    files = []
    try:
        for root, dirs, filenames in os.walk(workspace):
            dirs[:] = [d for d in dirs if d not in ignore_dirs and not d.startswith(".")]
            for f in sorted(filenames):
                if f.endswith((".pyc", ".pyo")):
                    continue
                rel = os.path.relpath(os.path.join(root, f), workspace).replace("\\", "/")
                files.append(rel)
        files.sort()
    except Exception:
        files = []

    return FileListResponse(files=files, workspace_path=workspace)


@router.get("/{project_id}/files/content", response_model=FileContentResponse)
async def get_file_content(
    project_id: uuid.UUID,
    file_path: str,
    current_user: CurrentUser,
    db: DBSession,
):
    from app.database.repositories.projects import ProjectRepository

    repo = ProjectRepository(db)
    project = await repo.get_by_id(project_id)
    if not project or str(project.user_id) != str(current_user.id):
        raise HTTPException(status_code=404, detail="Project not found.")

    workspace = project.workspace_path or f"/app/workspaces/{project_id}"
    if not os.path.exists(workspace):
        raise HTTPException(status_code=400, detail="Workspace not initialized.")

    clean_path = file_path.strip().lstrip("/\\")
    norm_path = os.path.normpath(clean_path)
    if norm_path.startswith("..") or os.path.isabs(norm_path):
        raise HTTPException(status_code=403, detail="Path traversal forbidden.")

    abs_path = os.path.join(workspace, norm_path)
    if not os.path.exists(abs_path) or os.path.isdir(abs_path):
        raise HTTPException(status_code=404, detail=f"File not found: {file_path}")

    try:
        with open(abs_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return FileContentResponse(
        path=clean_path,
        content=content,
        size_bytes=len(content.encode("utf-8")),
        language=_detect_language(clean_path),
    )


@router.get("/{project_id}/files/changes", response_model=list[FileChangeResponse])
async def get_file_changes(
    project_id: uuid.UUID,
    current_user: CurrentUser,
    db: DBSession,
    limit: int = 50,
):
    from app.database.models import FileChange
    from app.database.repositories.projects import ProjectRepository
    from sqlalchemy import select

    repo = ProjectRepository(db)
    project = await repo.get_by_id(project_id)
    if not project or str(project.user_id) != str(current_user.id):
        raise HTTPException(status_code=404, detail="Project not found.")

    result = await db.execute(
        select(FileChange)
        .where(FileChange.project_id == project_id)
        .order_by(FileChange.created_at.desc())
        .limit(limit)
    )
    changes = result.scalars().all()

    return [
        FileChangeResponse(
            file_path=c.file_path,
            change_type=c.change_type,
            before_content=c.before_content,
            after_content=c.after_content,
            reason=c.reason,
            agent=c.agent,
            timestamp=c.created_at.isoformat(),
        )
        for c in changes
    ]
