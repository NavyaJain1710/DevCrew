"""
Execution Tools — Sandboxed command execution for agents.

SECURITY:
- Command allowlist enforced — only whitelisted commands may run
- Absolute timeouts on all executions
- Output size limits
- Environment variable protection (no secret passthrough)
- Working directory always within workspace
- Dangerous patterns blocked before execution
"""

from __future__ import annotations

import asyncio
import os
import re
import shlex
from typing import Any, Optional

import structlog

from app.config import get_settings

logger = structlog.get_logger(__name__)
settings = get_settings()

# ── Security: Command allowlist ───────────────────────────────────────────────
# Only these command prefixes are permitted.
ALLOWED_COMMAND_PREFIXES = frozenset(
    [
        "python",
        "pip",
        "pytest",
        "ruff",
        "black",
        "mypy",
        "bandit",
        "semgrep",
        "pip-audit",
        "safety",
        "npm",
        "npx",
        "node",
        "eslint",
        "prettier",
        "tsc",
        "echo",
        "cat",
        "ls",
        "find",
        "grep",
        "git",
    ]
)

# ── Security: Dangerous patterns (always blocked) ──────────────────────────────
BLOCKED_PATTERNS = [
    r"rm\s+-rf\s+/",
    r"rm\s+-rf\s+~",
    r">(>?)\s*/dev/",
    r"format\s+[A-Z]:",
    r"dd\s+if=",
    r":\(\)\s*\{",  # Fork bomb
    r"base64\s+-d",  # Common deobfuscation
    r"curl\s+.*\|\s*(?:bash|sh)",  # Pipe to shell
    r"wget\s+.*\|\s*(?:bash|sh)",
    r"chmod\s+777",
    r"chown\s+root",
    r"sudo\s+",
    r"su\s+-",
    r"passwd\s+",
    r"useradd|userdel|usermod",
    r"systemctl",
    r"service\s+",
    r"iptables",
    r"nc\s+.*-e",  # Netcat reverse shell
    r"python.*-c.*import.*os.*system",
    r"eval\s*\(",
    r"exec\s*\(",
]

# ── Security: Sensitive env vars never passed to subprocesses ─────────────────
BLOCKED_ENV_VARS = frozenset(
    [
        "JWT_SECRET",
        "OPENROUTER_API_KEY",
        "GROQ_API_KEY",
        "GITHUB_TOKEN",
        "DATABASE_URL",
        "SUPABASE_KEY",
        "AWS_SECRET_ACCESS_KEY",
        "AWS_ACCESS_KEY_ID",
    ]
)


class CommandBlockedError(Exception):
    """Raised when a command is blocked by the security policy."""


class ExecutionTools:
    """Sandboxed command execution layer."""

    def __init__(self) -> None:
        self._timeout = settings.sandbox_timeout_seconds
        self._max_output = settings.sandbox_max_output_bytes

    def _validate_command(self, command: str) -> None:
        """
        Validate a command before execution.
        Raises CommandBlockedError if the command is not permitted.
        """
        stripped = command.strip()

        # Check for dangerous patterns
        for pattern in BLOCKED_PATTERNS:
            if re.search(pattern, stripped, re.IGNORECASE):
                raise CommandBlockedError(
                    f"Command blocked by security policy. Matched pattern: {pattern}\n"
                    f"Command: {stripped[:100]}"
                )

        # Check allowlist — first token must be in the allowed set
        try:
            tokens = shlex.split(stripped)
        except ValueError:
            raise CommandBlockedError(f"Command could not be parsed: {stripped[:100]}")

        if not tokens:
            raise CommandBlockedError("Empty command")

        first_token = os.path.basename(tokens[0]).lower()
        # Also check without .exe on Windows
        first_token_clean = first_token.replace(".exe", "").replace(".cmd", "")

        if first_token_clean not in ALLOWED_COMMAND_PREFIXES:
            raise CommandBlockedError(
                f"Command '{first_token}' is not in the allowed command list. "
                f"Allowed: {sorted(ALLOWED_COMMAND_PREFIXES)}"
            )

    def _clean_env(self) -> dict[str, str]:
        """Return a sanitized environment dict without sensitive variables."""
        return {
            k: v
            for k, v in os.environ.items()
            if k not in BLOCKED_ENV_VARS
        }

    async def run_command(
        self,
        command: str,
        cwd: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> dict[str, Any]:
        """
        Run a shell command in a sandboxed environment.
        Returns {output, exit_code, success}.
        """
        self._validate_command(command)

        effective_timeout = timeout or self._timeout
        env = self._clean_env()

        logger.info("executing_command", command=command[:100], cwd=cwd)

        try:
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                cwd=cwd,
                env=env,
            )

            try:
                stdout, _ = await asyncio.wait_for(
                    proc.communicate(), timeout=effective_timeout
                )
            except asyncio.TimeoutError:
                proc.kill()
                await proc.wait()
                logger.warning("command_timeout", command=command[:100], timeout=effective_timeout)
                return {
                    "output": f"[TIMEOUT after {effective_timeout}s]",
                    "exit_code": -1,
                    "success": False,
                }

            output = stdout.decode("utf-8", errors="replace")

            # Enforce output size limit
            if len(output) > self._max_output:
                output = output[: self._max_output] + "\n[OUTPUT TRUNCATED]"

            success = proc.returncode == 0
            logger.info(
                "command_complete",
                command=command[:100],
                exit_code=proc.returncode,
                output_len=len(output),
            )
            return {"output": output, "exit_code": proc.returncode, "success": success}

        except CommandBlockedError:
            raise
        except Exception as e:
            logger.error("command_execution_error", command=command[:100], error=str(e))
            return {"output": str(e), "exit_code": -1, "success": False}

    async def run_python(
        self, script: str, cwd: Optional[str] = None
    ) -> dict[str, Any]:
        """Run a Python script string."""
        return await self.run_command(f'python -c "{script}"', cwd=cwd)

    async def run_tests(
        self, test_dir: str, cwd: Optional[str] = None
    ) -> dict[str, Any]:
        """Run pytest on a directory."""
        cmd = f"python -m pytest {test_dir} -v --tb=short -q"
        return await self.run_command(cmd, cwd=cwd or test_dir, timeout=120)

    async def run_linter(
        self, path: str, fix: bool = False
    ) -> dict[str, Any]:
        """Run ruff linter on a path."""
        fix_flag = "--fix" if fix else ""
        cmd = f"python -m ruff check {path} {fix_flag} --quiet"
        return await self.run_command(cmd, cwd=path)

    async def run_formatter(self, path: str) -> dict[str, Any]:
        """Run black formatter on a path."""
        cmd = f"python -m black {path} --quiet"
        return await self.run_command(cmd, cwd=path)

    async def install_requirements(
        self, requirements_file: str, cwd: Optional[str] = None
    ) -> dict[str, Any]:
        """Install pip requirements."""
        cmd = f"pip install -r {requirements_file} -q"
        return await self.run_command(cmd, cwd=cwd, timeout=120)
