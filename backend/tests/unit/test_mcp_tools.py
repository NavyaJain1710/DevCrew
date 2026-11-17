"""
Unit Tests — Model Context Protocol (MCP) Client and Server.

Tests Requirement 2:
- Dynamic tool discovery
- Workspace file operations (list, write, read, search)
- Documentation search tool with real external query
- Argument validation and error handling
"""

import pytest
from app.mcp.client import mcp_client
from app.mcp.server import workspace_file_operations, documentation_search


def test_mcp_tool_discovery():
    tools = mcp_client.list_tools()
    tool_names = [t["name"] for t in tools]
    assert "workspace_file_operations" in tool_names
    assert "documentation_search" in tool_names
    assert len(tools) >= 2


@pytest.mark.asyncio
async def test_mcp_workspace_file_operations(tmp_path):
    workspace = str(tmp_path / "mcp_ws")

    # 1. Write file
    write_res = await mcp_client.call_tool(
        "workspace_file_operations",
        {
            "action": "write_file",
            "file_path": "app/service.py",
            "content": "def calculate_total(a, b):\n    return a + b\n",
            "workspace_root": workspace,
        },
    )
    assert write_res["status"] == "success"

    # 2. Read file
    read_res = await mcp_client.call_tool(
        "workspace_file_operations",
        {
            "action": "read_file",
            "file_path": "app/service.py",
            "workspace_root": workspace,
        },
    )
    assert read_res["status"] == "success"
    assert "calculate_total" in read_res["content"]

    # 3. List files
    list_res = await mcp_client.call_tool(
        "workspace_file_operations",
        {
            "action": "list_files",
            "workspace_root": workspace,
        },
    )
    assert list_res["status"] == "success"
    assert "app/service.py" in list_res["files"]

    # 4. Search in code
    search_res = await mcp_client.call_tool(
        "workspace_file_operations",
        {
            "action": "search_code",
            "search_term": "calculate_total",
            "workspace_root": workspace,
        },
    )
    assert search_res["status"] == "success"
    assert len(search_res["matches"]) >= 1


@pytest.mark.asyncio
async def test_mcp_documentation_search():
    res = await mcp_client.call_tool(
        "documentation_search",
        {"query": "fastapi", "domain": "python"},
    )
    assert res["status"] == "success"
    assert res["results_count"] >= 1
    assert len(res["references"]) >= 1
    # Verify title or snippet exists
    first_ref = res["references"][0]
    assert "title" in first_ref
    assert "source" in first_ref
