"""
WebSocket Hub — broadcasts real-time events to all connected clients
for a given project.

Events emitted:
  agent_started, agent_completed
  tool_started, tool_completed
  file_created, file_modified
  test_started, test_completed
  security_scan_started, security_scan_completed
  review_started
  project_completed
  human_approval_required
  approval_resolved
  error
"""

from __future__ import annotations

import asyncio
import json
from collections import defaultdict
from datetime import datetime
from typing import Any

import structlog
from fastapi import WebSocket

logger = structlog.get_logger(__name__)


class WebSocketHub:
    """
    Central hub for managing WebSocket connections grouped by project ID.
    Thread-safe via asyncio.
    """

    def __init__(self) -> None:
        # project_id → set of active WebSocket connections
        self._connections: dict[str, set[WebSocket]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def connect(self, project_id: str, ws: WebSocket) -> None:
        """Register a new WebSocket connection for a project."""
        await ws.accept()
        async with self._lock:
            self._connections[project_id].add(ws)
        logger.info("ws_connected", project_id=project_id, total=len(self._connections[project_id]))

    async def disconnect(self, project_id: str, ws: WebSocket) -> None:
        """Remove a WebSocket connection."""
        async with self._lock:
            self._connections[project_id].discard(ws)
            if not self._connections[project_id]:
                del self._connections[project_id]
        logger.info("ws_disconnected", project_id=project_id)

    async def broadcast(
        self,
        project_id: str,
        event: str,
        data: dict[str, Any],
    ) -> None:
        """
        Broadcast an event to all connected clients for a project.
        Dead connections are removed automatically.
        """
        message = json.dumps(
            {
                "event": event,
                "data": data,
                "timestamp": datetime.utcnow().isoformat(),
                "project_id": project_id,
            }
        )

        dead: set[WebSocket] = set()
        connections = set(self._connections.get(project_id, set()))

        for ws in connections:
            try:
                await ws.send_text(message)
            except Exception:
                dead.add(ws)

        # Clean up dead connections
        if dead:
            async with self._lock:
                self._connections[project_id] -= dead
                if not self._connections[project_id]:
                    self._connections.pop(project_id, None)

        logger.debug(
            "ws_broadcast",
            project_id=project_id,
            event_name=event,
            recipients=len(connections) - len(dead),
            dead=len(dead),
        )

    def active_connections(self, project_id: str) -> int:
        """Return the number of active connections for a project."""
        return len(self._connections.get(project_id, set()))


# Singleton hub instance — shared across the application
ws_hub = WebSocketHub()
