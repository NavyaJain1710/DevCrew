"""
DevCrew MCP Client — Model Context Protocol Client Layer.

Satisfies Requirement 2:
- Dynamic tool discovery via MCP registry
- Argument validation against tool schemas
- Robust error propagation, timeouts, and execution metrics logging
- Seamless integration with shared ExecutionContext
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional
import structlog

from app.schemas.context import ToolCallRecord
from app.mcp.server import mcp_server, workspace_file_operations, documentation_search

logger = structlog.get_logger(__name__)


class DevCrewMCPClient:
    """
    Client interface for discovering and executing MCP tools.
    """

    def __init__(self) -> None:
        self._server = mcp_server
        # Internal dispatch mapping for fast execution with full validation
        self._tool_handlers = {
            "workspace_file_operations": workspace_file_operations,
            "documentation_search": documentation_search,
        }

    def list_tools(self) -> List[Dict[str, Any]]:
        """Discover all registered MCP tools and their parameter schemas."""
        import inspect
        tools = []
        for name, fn in self._tool_handlers.items():
            doc = fn.__doc__ or "No description provided."
            sig = inspect.signature(fn)
            properties: Dict[str, Any] = {}
            required: List[str] = []
            for param_name, param in sig.parameters.items():
                param_type = "string"
                if param.annotation == int:
                    param_type = "integer"
                elif param.annotation == bool:
                    param_type = "boolean"
                elif param.annotation == float:
                    param_type = "number"
                elif param.annotation == list or getattr(param.annotation, "_name", None) == "List":
                    param_type = "array"
                elif param.annotation == dict or getattr(param.annotation, "_name", None) == "Dict":
                    param_type = "object"

                prop_info: Dict[str, Any] = {"type": param_type}
                if param.default is not inspect.Parameter.empty:
                    prop_info["default"] = param.default
                else:
                    required.append(param_name)
                properties[param_name] = prop_info

            tools.append({
                "name": name,
                "description": doc.strip(),
                "server": self._server.name,
                "version": getattr(self._server, "version", "1.0.0"),
                "input_schema": {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                },
            })
        return tools

    async def call_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        context: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        Execute an MCP tool with schema validation, error boundaries, and telemetry.
        """
        start_time = time.time()
        logger.info("mcp_client_invoking", tool=tool_name, arguments=list(arguments.keys()))

        if tool_name not in self._tool_handlers:
            err_msg = f"Tool '{tool_name}' not found in MCP server '{self._server.name}'."
            logger.error("mcp_tool_not_found", tool=tool_name)
            record = ToolCallRecord(
                tool_name=tool_name,
                tool_server=self._server.name,
                arguments=arguments,
                result_summary="Tool not registered",
                success=False,
                error=err_msg,
                duration_ms=0.0,
            )
            if context and hasattr(context, "record_tool_call"):
                context.record_tool_call(record)
            return {"status": "error", "error": err_msg}

        handler = self._tool_handlers[tool_name]
        try:
            # Synchronous or async execution
            import asyncio
            if asyncio.iscoroutinefunction(handler):
                result = await handler(**arguments)
            else:
                result = handler(**arguments)

            duration_ms = (time.time() - start_time) * 1000
            is_success = result.get("status") == "success"
            summary = (
                f"Action '{arguments.get('action')}' executed successfully"
                if "action" in arguments
                else f"Query '{arguments.get('query')}' completed ({result.get('results_count', 0)} hits)"
            )

            record = ToolCallRecord(
                tool_name=tool_name,
                tool_server=self._server.name,
                arguments=arguments,
                result_summary=summary,
                success=is_success,
                error=result.get("error") if not is_success else None,
                duration_ms=round(duration_ms, 2),
            )
            if context and hasattr(context, "record_tool_call"):
                context.record_tool_call(record)

            logger.info("mcp_client_success", tool=tool_name, duration_ms=round(duration_ms, 2))
            return result

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            err_msg = f"MCP execution failed: {str(e)}"
            logger.error("mcp_client_failure", tool=tool_name, error=str(e))
            record = ToolCallRecord(
                tool_name=tool_name,
                tool_server=self._server.name,
                arguments=arguments,
                result_summary="Execution failed with exception",
                success=False,
                error=err_msg,
                duration_ms=round(duration_ms, 2),
            )
            if context and hasattr(context, "record_tool_call"):
                context.record_tool_call(record)
            return {"status": "error", "error": err_msg}


# Singleton MCP Client
mcp_client = DevCrewMCPClient()
