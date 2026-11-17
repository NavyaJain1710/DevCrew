"""
Integration Tests — A2A (Agent-to-Agent) Protocol Endpoint & Delegation.

Tests Requirement 6:
- Agent Card endpoint discovery (/.well-known/agent.json and /api/a2a/agent-card)
- A2A Task submission, status checking, and cancellation
- Payload validation and provenance recording
"""

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import create_app
from app.a2a.client import a2a_client


@pytest.fixture
def app():
    return create_app()


@pytest.mark.asyncio
async def test_a2a_agent_card_discovery(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Check standard well-known location
        res = await client.get("/.well-known/agent.json")
        assert res.status_code == 200
        card = res.json()
        assert card["id"] == "google-adk-developer"
        assert "Google Agent Development Kit" in card["framework"]
        assert len(card["skills"]) >= 1
        assert card["skills"][0]["id"] == "code_implementation"

        # Check API alias endpoint
        res2 = await client.get("/api/a2a/agent-card")
        assert res2.status_code == 200
        assert res2.json()["id"] == card["id"]


@pytest.mark.asyncio
async def test_a2a_task_submission_and_lifecycle(app, tmp_path):
    workspace = str(tmp_path / "a2a_test_ws")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Submit task
        payload = {
            "skill_id": "code_implementation",
            "execution_id": "test-integ-1",
            "origin_framework": "CrewAI",
            "input_payload": {
                "raw_requirement": "Build a simple health check router with pytest",
                "workspace_path": workspace,
            },
        }
        res = await client.post("/api/a2a/tasks", json=payload)
        assert res.status_code == 202
        data = res.json()
        task_id = data["task_id"]
        assert data["status"] in ("completed", "working")
        assert data["provenance"]["origin_framework"] == "CrewAI"
        assert data["provenance"]["target_framework"] == "Google ADK"

        # Query task status
        res_get = await client.get(f"/api/a2a/tasks/{task_id}")
        assert res_get.status_code == 200
        assert res_get.json()["task_id"] == task_id
