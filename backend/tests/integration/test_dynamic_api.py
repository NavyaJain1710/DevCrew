"""
Integration Tests — Dynamic Documents & MCP Endpoints.

Tests:
- TEST 5: MCP Tool Discovery via API
- TEST 6: MCP Tool Execution via API
- TEST 7: MCP Tool Error Handling
- Dynamic Document Upload, Query, List, and Deletion via API
"""

import io
import uuid
import pytest
from httpx import ASGITransport, AsyncClient
from reportlab.pdfgen import canvas

from app.main import create_app
from app.api.auth import create_access_token
from app.database.base import AsyncSessionLocal
from app.database.models import User, UserRole, Project, ProjectStatus
from app.database.repositories.users import UserRepository
from app.database.repositories.projects import ProjectRepository


def _generate_pdf_bytes(text: str) -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf)
    c.drawString(100, 750, text)
    c.save()
    buf.seek(0)
    return buf.getvalue()


@pytest.fixture
def app():
    return create_app()


@pytest.mark.asyncio
async def test_api_mcp_discovery_and_execution(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # TEST 5: Real MCP Tool Discovery
        resp = await client.get("/api/mcp/tools")
        assert resp.status_code == 200
        tools = resp.json()
        assert len(tools) >= 2
        tool_names = [t["name"] for t in tools]
        assert "workspace_file_operations" in tool_names
        assert "documentation_search" in tool_names
        
        # Verify schema
        ws_tool = next(t for t in tools if t["name"] == "workspace_file_operations")
        assert "input_schema" in ws_tool
        assert "properties" in ws_tool["input_schema"]

        # TEST 6: Real MCP Tool Execution
        exec_resp = await client.post(
            "/api/mcp/execute",
            json={
                "tool_name": "documentation_search",
                "arguments": {"query": "fastapi", "domain": "python"},
            },
        )
        assert exec_resp.status_code == 200
        data = exec_resp.json()
        assert data["status"] == "success"
        assert data["tool_name"] == "documentation_search"
        assert data["result"]["status"] == "success"

        # TEST 7: Real MCP Tool Error Handling
        err_resp = await client.post(
            "/api/mcp/execute",
            json={
                "tool_name": "workspace_file_operations",
                "arguments": {"action": "unsupported_action"},
            },
        )
        assert err_resp.status_code == 200
        err_data = err_resp.json()
        assert err_data["status"] == "error"
        assert "Unsupported file action" in err_data["error"]


@pytest.mark.asyncio
async def test_api_document_lifecycle(app):
    # Setup test user and project in DB
    user_id = uuid.uuid4()
    proj_id = uuid.uuid4()
    async with AsyncSessionLocal() as db:
        user_repo = UserRepository(db)
        user = await user_repo.create(
            email=f"doc-user-{user_id.hex[:6]}@example.com",
            hashed_password="hashed_pw_dummy",
            full_name="Doc Tester",
        )
        await db.commit()
        user_id = user.id

        proj_repo = ProjectRepository(db)
        proj = await proj_repo.create(
            user_id=user_id,
            name="RAG Test Project",
            description="Testing dynamic RAG file upload",
            raw_requirement="Build a task manager with authentication",
        )
        await db.commit()
        proj_id = proj.id

    token = create_access_token(str(user_id))
    auth_headers = {"Authorization": f"Bearer {token}"}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Upload PDF and Python file
        pdf_bytes = _generate_pdf_bytes("Enterprise OAuth2 Security Architecture and JWT validation guidelines.")
        code_bytes = b"def verify_password(plain, hashed):\n    return bcrypt.checkpw(plain, hashed)\n"

        files = [
            ("files", ("security_guide.pdf", pdf_bytes, "application/pdf")),
            ("files", ("crypto_utils.py", code_bytes, "text/x-python")),
        ]

        upload_res = await client.post(
            f"/api/projects/{proj_id}/documents/upload",
            headers=auth_headers,
            files=files,
        )
        assert upload_res.status_code == 201
        upload_data = upload_res.json()
        assert len(upload_data) == 2
        assert upload_data[0]["status"] == "indexed"
        assert upload_data[0]["filename"] == "security_guide.pdf"
        assert upload_data[0]["embedding_dimension"] == 384
        pdf_doc_id = upload_data[0]["doc_id"]

        # 2. List documents
        list_res = await client.get(
            f"/api/projects/{proj_id}/documents",
            headers=auth_headers,
        )
        assert list_res.status_code == 200
        docs = list_res.json()
        assert len(docs) >= 2
        doc_names = [d["filename"] for d in docs]
        assert "security_guide.pdf" in doc_names
        assert "crypto_utils.py" in doc_names

        # 3. Query documents dynamically
        query_res = await client.post(
            f"/api/projects/{proj_id}/documents/query",
            headers=auth_headers,
            json={"query": "OAuth2 Security Architecture", "top_k": 2},
        )
        assert query_res.status_code == 200
        hits = query_res.json()
        assert len(hits) >= 1
        assert hits[0]["title"] == "security_guide.pdf"
        assert hits[0]["score"] > 0.15

        # 4. Delete document
        del_res = await client.delete(
            f"/api/projects/{proj_id}/documents/{pdf_doc_id}",
            headers=auth_headers,
        )
        assert del_res.status_code == 200
        assert del_res.json()["status"] == "deleted"

        # 5. Verify deletion
        list_after_del = await client.get(
            f"/api/projects/{proj_id}/documents",
            headers=auth_headers,
        )
        remaining_names = [d["filename"] for d in list_after_del.json()]
        assert "security_guide.pdf" not in remaining_names
