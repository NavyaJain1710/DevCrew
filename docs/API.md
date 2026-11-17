# DevCrew — REST API Specification & Endpoint Guide

The DevCrew backend exposes a fully typed, asynchronous REST API powered by **FastAPI** with automatic OpenAPI (Swagger) documentation available at `/docs`.

---

## 1. Authentication & Users (`/api/auth`)

| Method | Path | Summary | Auth Required |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/auth/register` | Register a new user account | No |
| `POST` | `/api/auth/login` | Login and obtain JWT access token | No |
| `GET` | `/api/auth/me` | Fetch authenticated user profile | Bearer JWT |

---

## 2. Projects & Autonomous Pipeline (`/api/projects`)

| Method | Path | Summary | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/projects/` | List all user projects | Returns list of projects owned by current user |
| `POST` | `/api/projects/` | Create a new project | Allocates project ID, workspace directory, and status `CREATED` |
| `GET` | `/api/projects/{id}` | Get project details | Returns project metadata, requirements, and execution stats |
| `POST` | `/api/projects/{id}/run` | Start autonomous execution | Launches the multi-agent pipeline (CrewAI + Google ADK via A2A) |
| `GET` | `/api/projects/{id}/events` | SSE Real-time execution stream | Server-Sent Events stream emitting live agent progress & logs |
| `GET` | `/api/projects/{id}/files` | List project workspace files | Discovers files created by agents in the workspace |
| `GET` | `/api/projects/{id}/files/content` | Read workspace file content | Safely retrieves file text with path-traversal guardrails |
| `GET` | `/api/projects/{id}/download` | Download ZIP archive | Packages the generated project codebase as a downloadable `.zip` |

---

## 3. Dynamic RAG Knowledge Base (`/api/projects/{id}/documents`)

| Method | Path | Summary | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/{id}/documents/upload` | Upload & index documents | Parses PDF, DOCX, Code, or Markdown and indexes dense vector chunks into ChromaDB |
| `GET` | `/{id}/documents` | List indexed project documents | Returns all distinct indexed files with vector chunk counts and SHA-256 hashes |
| `DELETE`| `/{id}/documents/{doc_id}` | Delete document | Purges all vector embeddings belonging to document with multi-tenant isolation |
| `POST` | `/{id}/documents/query` | Semantic vector search | Encodes natural language query into 384d vector and retrieves nearest matches |
| `POST` | `/{id}/documents/index-workspace`| Index workspace code | Recursively scans project workspace and indexes all code & config files |

---

## 4. Model Context Protocol (MCP) Tools (`/api/mcp`)

| Method | Path | Summary | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/mcp/tools` | Discover MCP tools | Dynamically introspects registered FastMCP tools, schemas, and descriptions |
| `POST` | `/api/mcp/execute` | Execute MCP tool | Executes a tool (`workspace_file_operations`, `documentation_search`) with validated arguments |

---

## 5. Agent-to-Agent (A2A) Protocol (`/.well-known` & `/api/a2a`)

| Method | Path | Summary | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/.well-known/agent.json` | A2A Agent Card Discovery | Standards-compliant Agent Card advertising Google ADK capabilities and schemas |
| `POST` | `/api/a2a/tasks` | Submit A2A task | Asynchronously dispatches a code generation/testing task to Google ADK |
| `GET` | `/api/a2a/tasks/{task_id}` | Poll A2A task status | Returns task state (`SUBMITTED`, `WORKING`, `COMPLETED`, `FAILED`) and result payload |

---

## 6. System & Health

| Method | Path | Summary |
| :--- | :--- | :--- |
| `GET` | `/` | Service information, docs link, and frontend dashboard URL |
| `GET` | `/health` | Service health status and database connectivity check |

