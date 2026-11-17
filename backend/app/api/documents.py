"""
Documents & RAG API — Upload, index, list, delete, and query project knowledge base.

Satisfies Requirements:
- Multi-format file uploads (PDF, DOCX, TXT, MD, Python/JS/TS code)
- Dynamic ChromaDB indexing and vector search
- Strict tenant and workspace isolation
- Incremental indexing and vector removal on deletion
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel

from app.dependencies import CurrentUser, DBSession
from app.database.repositories.projects import ProjectRepository
from app.rag.service import rag_service

router = APIRouter(prefix="/projects", tags=["Documents & RAG"])


class DocumentUploadResponse(BaseModel):
    status: str
    doc_id: Optional[str]
    filename: str
    file_type: str
    chunk_count: int
    embedding_dimension: Optional[int] = None
    character_count: Optional[int] = None
    message: Optional[str] = None


class DocumentItem(BaseModel):
    doc_id: str
    filename: str
    file_type: str
    chunk_count: int
    sha256: str


class DocumentQueryRequest(BaseModel):
    query: str
    top_k: int = 3
    similarity_threshold: float = 0.35


class DocumentQueryResult(BaseModel):
    document_id: str
    title: str
    source_type: str
    content_snippet: str
    score: float
    metadata: Dict[str, Any]


@router.post(
    "/{project_id}/documents/upload",
    response_model=List[DocumentUploadResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Upload and index files (PDF, DOCX, Code, Markdown) into project vector DB",
)
async def upload_documents(
    project_id: uuid.UUID,
    files: List[UploadFile] = File(...),
    chunk_size: int = Form(500),
    chunk_overlap: int = Form(50),
    current_user: CurrentUser = None,
    db: DBSession = None,
) -> List[DocumentUploadResponse]:
    repo = ProjectRepository(db)
    project = await repo.get_by_id(project_id)
    if not project or str(project.user_id) != str(current_user.id):
        raise HTTPException(status_code=404, detail="Project not found.")

    results: List[DocumentUploadResponse] = []

    for f in files:
        content = await f.read()
        if not content:
            continue
        try:
            res = rag_service.index_document(
                content=content,
                filename=f.filename or "uploaded_file",
                user_id=str(current_user.id),
                project_id=str(project_id),
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
            )
            results.append(
                DocumentUploadResponse(
                    status=res.get("status", "indexed"),
                    doc_id=res.get("doc_id"),
                    filename=res.get("filename", f.filename),
                    file_type=res.get("file_type", "document"),
                    chunk_count=res.get("chunk_count", 0),
                    embedding_dimension=res.get("embedding_dimension"),
                    character_count=res.get("character_count"),
                    message=res.get("reason"),
                )
            )
        except Exception as e:
            results.append(
                DocumentUploadResponse(
                    status="error",
                    doc_id=None,
                    filename=f.filename or "error",
                    file_type="unknown",
                    chunk_count=0,
                    message=str(e),
                )
            )

    return results


@router.get(
    "/{project_id}/documents",
    response_model=List[DocumentItem],
    summary="List all indexed documents for this project",
)
async def list_documents(
    project_id: uuid.UUID,
    current_user: CurrentUser,
    db: DBSession,
) -> List[DocumentItem]:
    repo = ProjectRepository(db)
    project = await repo.get_by_id(project_id)
    if not project or str(project.user_id) != str(current_user.id):
        raise HTTPException(status_code=404, detail="Project not found.")

    docs = rag_service.list_project_documents(
        user_id=str(current_user.id),
        project_id=str(project_id),
    )
    return [
        DocumentItem(
            doc_id=d["doc_id"],
            filename=d["filename"],
            file_type=d["file_type"],
            chunk_count=d["chunk_count"],
            sha256=d["sha256"],
        )
        for d in docs
    ]


@router.delete(
    "/{project_id}/documents/{doc_id}",
    summary="Delete a document and purge its vectors from ChromaDB",
)
async def delete_document(
    project_id: uuid.UUID,
    doc_id: str,
    current_user: CurrentUser,
    db: DBSession,
) -> Dict[str, Any]:
    repo = ProjectRepository(db)
    project = await repo.get_by_id(project_id)
    if not project or str(project.user_id) != str(current_user.id):
        raise HTTPException(status_code=404, detail="Project not found.")

    deleted_count = rag_service.delete_document(
        doc_id=doc_id,
        user_id=str(current_user.id),
        project_id=str(project_id),
    )
    if deleted_count == 0:
        raise HTTPException(status_code=404, detail="Document not found or already deleted.")

    return {"status": "deleted", "doc_id": doc_id, "vectors_removed": deleted_count}


@router.post(
    "/{project_id}/documents/query",
    response_model=List[DocumentQueryResult],
    summary="Perform dynamic semantic search on project documents",
)
async def query_documents(
    project_id: uuid.UUID,
    body: DocumentQueryRequest,
    current_user: CurrentUser,
    db: DBSession,
) -> List[DocumentQueryResult]:
    repo = ProjectRepository(db)
    project = await repo.get_by_id(project_id)
    if not project or str(project.user_id) != str(current_user.id):
        raise HTTPException(status_code=404, detail="Project not found.")

    refs = rag_service.retrieve(
        query=body.query,
        user_id=str(current_user.id),
        project_id=str(project_id),
        top_k=body.top_k,
        similarity_threshold=body.similarity_threshold,
    )

    return [
        DocumentQueryResult(
            document_id=r.document_id,
            title=r.title,
            source_type=r.source_type,
            content_snippet=r.content_snippet,
            score=r.score,
            metadata=r.metadata,
        )
        for r in refs
    ]


@router.post(
    "/{project_id}/documents/index-workspace",
    summary="Index all source files from the project workspace into ChromaDB",
)
async def index_workspace(
    project_id: uuid.UUID,
    current_user: CurrentUser,
    db: DBSession,
) -> Dict[str, Any]:
    repo = ProjectRepository(db)
    project = await repo.get_by_id(project_id)
    if not project or str(project.user_id) != str(current_user.id):
        raise HTTPException(status_code=404, detail="Project not found.")

    if not project.workspace_path:
        raise HTTPException(status_code=400, detail="No workspace path allocated for this project yet.")

    results = rag_service.index_workspace(
        workspace_path=project.workspace_path,
        user_id=str(current_user.id),
        project_id=str(project_id),
    )

    return {"status": "indexed", "total_files_indexed": len(results), "files": results}

