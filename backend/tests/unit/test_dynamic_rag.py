"""
Unit & Integration Tests — Dynamic RAG Pipeline.

Verifies Requirements:
- TEST 1: Dynamic RAG Document Indexing (PDF, DOCX, Code)
- TEST 2: Dynamic RAG Semantic Retrieval
- TEST 3: Dynamic RAG Empty State Handling
- TEST 4: Dynamic RAG Incremental Updates and Deletions
- TEST 10: Multi-User / Multi-Workspace Tenant Isolation
"""

import io
import pytest
from reportlab.pdfgen import canvas
import docx

from app.rag.service import RAGService, DocumentExtractor, TextChunker


def _generate_test_pdf(text: str) -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf)
    c.drawString(100, 750, text)
    c.save()
    buf.seek(0)
    return buf.getvalue()


def _generate_test_docx(text: str) -> bytes:
    doc = docx.Document()
    doc.add_paragraph(text)
    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf.getvalue()


@pytest.fixture
def rag_service(tmp_path):
    chroma_dir = str(tmp_path / "test_chroma")
    return RAGService(persist_dir=chroma_dir)


def test_document_extractor_pdf():
    pdf_bytes = _generate_test_pdf("DevCrew PDF Architecture Guide for Microservices")
    extracted = DocumentExtractor.extract("architecture.pdf", pdf_bytes)
    assert "DevCrew PDF Architecture Guide" in extracted


def test_document_extractor_docx():
    docx_bytes = _generate_test_docx("DevCrew DOCX Security Standard: enforce TLS 1.3")
    extracted = DocumentExtractor.extract("security.docx", docx_bytes)
    assert "DevCrew DOCX Security Standard" in extracted


def test_document_extractor_code():
    code_bytes = b"def authenticate_user(token: str) -> bool:\n    return len(token) > 10\n"
    extracted = DocumentExtractor.extract("auth.py", code_bytes)
    assert "def authenticate_user" in extracted


def test_text_chunker():
    long_text = "Paragraph One.\n\nParagraph Two with more details.\n\nParagraph Three concluding the topic."
    chunks = TextChunker.chunk(long_text, chunk_size=40, chunk_overlap=10)
    assert len(chunks) >= 2
    for c in chunks:
        assert "chunk_index" in c
        assert "text" in c
        assert len(c["text"]) > 0


# TEST 1: Dynamic RAG Document Indexing (PDF, DOCX, Code)
def test_dynamic_rag_indexing(rag_service):
    user_id = "user-100"
    project_id = "proj-100"

    # 1. PDF
    pdf_bytes = _generate_test_pdf("PostgreSQL database connection pooling with asyncpg and SQLAlchemy 2.0")
    pdf_res = rag_service.index_document(pdf_bytes, "db_guide.pdf", user_id, project_id)
    assert pdf_res["status"] == "indexed"
    assert pdf_res["chunk_count"] >= 1
    assert pdf_res["embedding_dimension"] == 384
    assert pdf_res["file_type"] == ".pdf"

    # 2. DOCX
    docx_bytes = _generate_test_docx("FastAPI dependency injection with Bearer token authentication")
    docx_res = rag_service.index_document(docx_bytes, "auth_specs.docx", user_id, project_id)
    assert docx_res["status"] == "indexed"
    assert docx_res["chunk_count"] >= 1
    assert docx_res["embedding_dimension"] == 384
    assert docx_res["file_type"] == ".docx"

    # 3. Code file
    code_bytes = b"class RedisCache:\n    def get(self, key: str):\n        return self.store.get(key)\n"
    code_res = rag_service.index_document(code_bytes, "cache.py", user_id, project_id)
    assert code_res["status"] == "indexed"
    assert code_res["chunk_count"] >= 1
    assert code_res["file_type"] == ".py"


# TEST 2: Dynamic RAG Semantic Retrieval
def test_dynamic_rag_retrieval(rag_service):
    user_id = "user-200"
    project_id = "proj-200"

    # Index doc
    pdf_bytes = _generate_test_pdf("Pytest integration testing guidelines for REST APIs and async endpoints")
    rag_service.index_document(pdf_bytes, "testing_guidelines.pdf", user_id, project_id)

    # Search for testing
    matches = rag_service.retrieve(
        query="How should we structure automated pytest test suites?",
        user_id=user_id,
        project_id=project_id,
        top_k=2,
        similarity_threshold=0.15,
    )
    assert len(matches) >= 1
    top = matches[0]
    assert top.title == "testing_guidelines.pdf"
    assert top.source_type == ".pdf"
    assert top.score > 0.15
    assert "Pytest integration testing guidelines" in top.content_snippet


# TEST 3: Dynamic RAG Empty State Handling
def test_dynamic_rag_empty_state_handling(rag_service):
    user_id = "user-300"
    project_id = "proj-300"

    # Index doc about quantum physics
    code_bytes = b"def compute_spin(state): return state * 0.5\n"
    rag_service.index_document(code_bytes, "quantum.py", user_id, project_id)

    # Search query completely unrelated with high threshold
    results = rag_service.retrieve(
        query="cooking gourmet Italian pizza with tomato sauce and mozzarella",
        user_id=user_id,
        project_id=project_id,
        top_k=2,
        similarity_threshold=0.60,
    )
    assert results == []


# TEST 4: Incremental Updates and Deletions
def test_dynamic_rag_updates_and_deletions(rag_service):
    user_id = "user-400"
    project_id = "proj-400"

    # Ingest version 1
    text_v1 = b"API Rate Limit: 100 requests per minute."
    res1 = rag_service.index_document(text_v1, "ratelimit.txt", user_id, project_id)
    assert res1["status"] == "indexed"
    doc_id = res1["doc_id"]

    # Ingest duplicate v1 -> skipped
    res_dup = rag_service.index_document(text_v1, "ratelimit.txt", user_id, project_id)
    assert res_dup["status"] == "skipped"

    # Ingest modified version 2
    text_v2 = b"API Rate Limit: 500 requests per minute with Redis sliding window."
    res2 = rag_service.index_document(text_v2, "ratelimit.txt", user_id, project_id)
    assert res2["status"] == "indexed"

    # Query for Redis
    matches = rag_service.retrieve("Redis sliding window", user_id=user_id, project_id=project_id, top_k=1)
    assert len(matches) == 1
    assert "500 requests" in matches[0].content_snippet

    # Delete document
    deleted_vectors = rag_service.delete_document(res2["doc_id"], user_id, project_id)
    assert deleted_vectors >= 1

    # Verify document is no longer retrievable
    after_delete = rag_service.retrieve("Redis sliding window", user_id=user_id, project_id=project_id, top_k=1)
    assert len(after_delete) == 0


# TEST 10: Multi-User / Multi-Workspace Tenant Isolation
def test_multi_user_isolation(rag_service):
    # User A indexes secret proprietary specs
    user_a = "user-alice-001"
    proj_a = "proj-alice-secret"
    rag_service.index_document(
        b"CONFIDENTIAL: Project Apollo private cryptographic encryption keys and AES-GCM secrets.",
        "secrets.txt",
        user_a,
        proj_a,
    )

    # User B indexes public recipes
    user_b = "user-bob-002"
    proj_b = "proj-bob-public"
    rag_service.index_document(
        b"Public Documentation: Open Source Web Application guidelines.",
        "public.txt",
        user_b,
        proj_b,
    )

    # User B queries for confidential encryption keys
    bob_query = rag_service.retrieve(
        query="What are the Project Apollo private cryptographic encryption keys?",
        user_id=user_b,
        project_id=proj_b,
        top_k=5,
        similarity_threshold=0.10,
    )
    # User B MUST NOT see User A's confidential documents!
    for ref in bob_query:
        assert "CONFIDENTIAL" not in ref.content_snippet
        assert ref.title != "secrets.txt"

    # User A CAN see their own document
    alice_query = rag_service.retrieve(
        query="Project Apollo cryptographic encryption keys",
        user_id=user_a,
        project_id=proj_a,
        top_k=1,
        similarity_threshold=0.10,
    )
    assert len(alice_query) == 1
    assert alice_query[0].title == "secrets.txt"

