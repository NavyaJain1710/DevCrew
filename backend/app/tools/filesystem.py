"""
File System Tools — Sandboxed file operations for agents.

SECURITY: All paths are validated to be within the project workspace.
Path traversal attacks are blocked.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Optional

import aiofiles
import structlog

logger = structlog.get_logger(__name__)


class PathViolationError(Exception):
    """Raised when a path escapes the sandbox boundary."""


class FileSystemTools:
    """
    Secure file system operations restricted to the project workspace.
    Agents must use these methods — never direct os/pathlib calls.
    """

    def __init__(self, sandbox_root: Optional[str] = None) -> None:
        self._sandbox_root = sandbox_root  # Set per-project when known

    def _validate_path(self, path: str, workspace: Optional[str] = None) -> Path:
        """
        Ensure the path is within the allowed workspace.
        Raises PathViolationError if the path escapes the sandbox.
        """
        root = workspace or self._sandbox_root
        if not root:
            # No sandbox configured — allow but warn
            logger.warning("filesystem_no_sandbox", path=path)
            return Path(path).resolve()

        resolved = Path(path).resolve()
        sandbox = Path(root).resolve()

        if not str(resolved).startswith(str(sandbox)):
            raise PathViolationError(
                f"Path '{resolved}' is outside the workspace sandbox '{sandbox}'. "
                "Direct filesystem access outside the workspace is not permitted."
            )
        return resolved

    async def read_file(self, path: str, workspace: Optional[str] = None) -> str:
        """Read file content as text."""
        safe_path = self._validate_path(path, workspace)
        if not safe_path.exists():
            raise FileNotFoundError(f"File not found: {safe_path}")
        async with aiofiles.open(safe_path, "r", encoding="utf-8", errors="replace") as f:
            content = await f.read()
        logger.debug("file_read", path=str(safe_path), size=len(content))
        return content

    async def write_file(
        self, path: str, content: str, workspace: Optional[str] = None
    ) -> None:
        """Write content to a file. Creates parent directories if needed."""
        safe_path = self._validate_path(path, workspace)
        safe_path.parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(safe_path, "w", encoding="utf-8") as f:
            await f.write(content)
        logger.info("file_written", path=str(safe_path), size=len(content))

    async def create_file(
        self, path: str, content: str = "", workspace: Optional[str] = None
    ) -> None:
        """Create a new file (fails if it already exists)."""
        safe_path = self._validate_path(path, workspace)
        if safe_path.exists():
            raise FileExistsError(f"File already exists: {safe_path}")
        await self.write_file(path, content, workspace)

    async def delete_file(self, path: str, workspace: Optional[str] = None) -> None:
        """Delete a file."""
        safe_path = self._validate_path(path, workspace)
        if safe_path.exists():
            safe_path.unlink()
            logger.info("file_deleted", path=str(safe_path))

    async def list_directory(
        self, path: str, workspace: Optional[str] = None, max_depth: int = 3
    ) -> list[str]:
        """List directory contents recursively up to max_depth."""
        safe_path = self._validate_path(path, workspace)
        if not safe_path.is_dir():
            return []

        result = []
        for root, dirs, files in os.walk(safe_path):
            # Compute depth
            depth = str(root).replace(str(safe_path), "").count(os.sep)
            if depth >= max_depth:
                dirs[:] = []  # Stop descending
                continue

            # Skip hidden dirs and common noise
            dirs[:] = [
                d for d in dirs
                if not d.startswith(".")
                and d not in {"node_modules", "__pycache__", ".venv", "venv", ".git", "dist", "build"}
            ]

            for f in files:
                rel = os.path.relpath(os.path.join(root, f), safe_path)
                result.append(rel)

        return sorted(result)

    async def search_files(
        self,
        root: str,
        pattern: str,
        workspace: Optional[str] = None,
    ) -> list[str]:
        """Search for files matching a glob pattern."""
        safe_root = self._validate_path(root, workspace)
        matches = list(safe_root.rglob(pattern))
        return [str(m.relative_to(safe_root)) for m in matches]

    async def apply_patch(
        self,
        path: str,
        old_content: str,
        new_content: str,
        workspace: Optional[str] = None,
    ) -> None:
        """Apply a targeted replacement patch to a file."""
        current = await self.read_file(path, workspace)
        if old_content not in current:
            raise ValueError(
                f"Patch target not found in {path}. The file may have changed."
            )
        patched = current.replace(old_content, new_content, 1)
        await self.write_file(path, patched, workspace)
        logger.info("patch_applied", path=path, old_len=len(old_content), new_len=len(new_content))

    async def copy_file(
        self,
        src: str,
        dest: str,
        workspace: Optional[str] = None,
    ) -> None:
        """Copy a file within the workspace."""
        safe_src = self._validate_path(src, workspace)
        safe_dest = self._validate_path(dest, workspace)
        safe_dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(safe_src, safe_dest)
        logger.info("file_copied", src=str(safe_src), dest=str(safe_dest))

    def file_exists(self, path: str, workspace: Optional[str] = None) -> bool:
        """Check if a file exists."""
        try:
            safe_path = self._validate_path(path, workspace)
            return safe_path.exists()
        except PathViolationError:
            return False
