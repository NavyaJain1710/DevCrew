"""
MCP API Router — Dynamic tool discovery, schema inspection, and live execution.

Satisfies Requirements:
- Discover all registered FastMCP tools with names, descriptions, and JSON schemas
- Live execution of workspace and documentation tools with validation
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.dependencies import CurrentUser
from app.mcp.client import mcp_client

router = APIRouter(prefix="/mcp", tags=["Model Context Protocol (MCP)"])


class MCPToolSchema(BaseModel):
    name: str
    description: str
    server: str
    version: str
    input_schema: Dict[str, Any]


class MCPExecuteRequest(BaseModel):
    tool_name: str
    arguments: Dict[str, Any]


class MCPExecuteResponse(BaseModel):
    status: str
    tool_name: str
    result: Dict[str, Any]
    error: Optional[str] = None


@router.get(
    "/tools",
    response_model=List[MCPToolSchema],
    summary="Discover all registered MCP tools and their parameter schemas",
)
async def list_tools() -> List[MCPToolSchema]:
    tools = mcp_client.list_tools()
    return [
        MCPToolSchema(
            name=t["name"],
            description=t["description"],
            server=t["server"],
            version=t["version"],
            input_schema=t["input_schema"],
        )
        for t in tools
    ]


@router.post(
    "/execute",
    response_model=MCPExecuteResponse,
    summary="Execute a registered MCP tool",
)
async def execute_tool(
    body: MCPExecuteRequest,
) -> MCPExecuteResponse:
    res = await mcp_client.call_tool(body.tool_name, body.arguments)
    is_success = res.get("status") == "success"
    return MCPExecuteResponse(
        status="success" if is_success else "error",
        tool_name=body.tool_name,
        result=res,
        error=res.get("error") if not is_success else None,
    )
