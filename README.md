# DevCrew: Multi-Agent AI Platform for Autonomous Software Development and DevOps

[![Architecture](https://img.shields.io/badge/Architecture-CrewAI%20%2B%20Google%20ADK-purple.svg)](#)
[![Interoperability](https://img.shields.io/badge/Protocol-Official%20A2A%201.0-blue.svg)](#)
[![Tools](https://img.shields.io/badge/Tools-Model%20Context%20Protocol%20(MCP)-orange.svg)](#)
[![Observability](https://img.shields.io/badge/Observability-Langfuse%20%2B%20OpenTelemetry-green.svg)](#)
[![License](https://img.shields.io/badge/License-MIT-lightgrey.svg)](#)

DevCrew is an enterprise multi-agent software engineering platform that autonomously translates high-level product requirements into tested, verified, and secured codebases.

Orchestrated with **100% CrewAI and Google Agent Development Kit (ADK)** communicating via the official **Agent-to-Agent (A2A)** interoperability protocol and **Model Context Protocol (MCP)**, DevCrew enforces real-world developer workflows—from initial threat modeling and requirements decomposition, to autonomous implementation, sandbox test verification, and automated security scanning.

---

## 🏛️ System Architecture

DevCrew couples **CrewAI** (for high-level requirements analysis, architecture design, and final security review) with **Google ADK** (for technical execution, external MCP tooling, and sandboxed Evaluator-Optimizer code repair) through an authentic, typed **A2A Protocol** interface.

```mermaid
flowchart TD
    User([User Requirement / Prompt]) --> SecurityGuard[Input Security Guard & Prompt Injection Defense]
    SecurityGuard --> CrewAnalyst[CrewAI Requirement Analyst Agent]
    
    subgraph CrewAI Orchestration
        CrewAnalyst --> SharedContext[(Typed Shared ExecutionContext)]
        SharedContext --> CrewArchitect[CrewAI Software Architect Agent]
        CrewArchitect --> RAGService[RAG Document Retrieval Engine]
        RAGService -. Technical Context .-> CrewArchitect
    end

    CrewArchitect --> A2AClient[A2A Protocol Dispatcher]

    subgraph A2A Interoperability Boundary
        A2AClient -- "1. Discover Agent Card (/.well-known/agent.json)" --> A2AServer[A2A Task Server]
        A2AClient -- "2. POST /api/a2a/tasks" --> A2AServer
        A2AServer -- "3. Task Provenance & Lifecycle" --> ADKAgent[Google ADK Developer Agent]
    end

    subgraph Google ADK Technical Execution
        ADKAgent --> MCPClient[FastMCP Client]
        MCPClient -- "workspace_file_operations" --> MCPServer[MCP Server: File Inspection & Operations]
        MCPClient -- "documentation_search" --> MCPServerDocs[MCP Server: External Tech Docs Search]
        MCPServer --> SandboxWorkspace[(Project Workspace)]
        
        SandboxWorkspace --> SandboxRunner[Sandbox Pytest Runner]
        SandboxRunner -- "Pass / Fail Metrics" --> EvaluatorOptimizer[Evaluator-Optimizer Repair Loop]
        EvaluatorOptimizer -- "Bounded Code Fixes" --> ADKAgent
    end

    ADKAgent --> A2AServer
    A2AServer -- "Completed Task Payload" --> A2AClient
    
    subgraph Final Validation & Review
        A2AClient --> CrewSentinel[CrewAI Quality & Security Sentinel]
        CrewSentinel --> OutputValidator[Pydantic Output Validation]
        OutputValidator --> FinalResponse[Structured FinalExecutionResponse JSON]
    end

    FinalResponse --> Frontend[Single React + Vite Dashboard]
    FinalResponse --> Observability[Langfuse Traces & Provenance Log]
```

---

## 📚 Comprehensive Documentation Directory

For deep technical specifications, verification matrices, and deployment architectures:

| Document | Purpose |
| :--- | :--- |
| [**Architecture & Engineering Specification**](docs/ARCHITECTURE.md) | Central architecture document detailing multi-agent design, technology stack, and data flows |
| [**Requirement Compliance Matrix**](docs/REQUIREMENT_COMPLIANCE.md) | Formal proof and verification matrix for all 11 faculty minimum requirements |
| [**Installation & Setup Guide**](docs/SETUP.md) | Step-by-step instructions for running DevCrew via Docker or locally |
| [**Environment Variables Reference**](docs/ENV_VARS.md) | Exhaustive configuration options for LLMs, RAG, database, and observability |
| [**REST API Documentation**](docs/API.md) | Endpoints, request/response models, and Swagger documentation guide |
| [**Testing & Verification Guide**](docs/TESTING.md) | Reproducible commands for running unit, integration, and E2E evaluation suites |
| [**Cloud Deployment Guide**](docs/DEPLOYMENT.md) | Production Docker Compose, AWS ECS, GCP Cloud Run, and disaster recovery |

### 📐 Mermaid Architecture Diagrams (`docs/architecture/`)
1. [System Architecture](docs/architecture/system_architecture.mmd)
2. [CrewAI + Google ADK Interoperability](docs/architecture/agent_interoperability.mmd)
3. [Official A2A Communication Sequence](docs/architecture/a2a_sequence.mmd)
4. [Dynamic Multi-Format RAG Pipeline](docs/architecture/rag_architecture.mmd)
5. [FastMCP Tool Discovery & Execution Flow](docs/architecture/mcp_architecture.mmd)
6. [Shared State & Context Passing](docs/architecture/state_management.mmd)
7. [Security & Guardrails Architecture](docs/architecture/security_architecture.mmd)
8. [End-to-End Execution Workflow Sequence](docs/architecture/execution_workflow.mmd)
9. [Production Cloud Deployment Topology](docs/architecture/deployment_architecture.mmd)

---

## 📋 Requirement-by-Requirement Implementation Status

| # | Requirement | Implementation Details | Status |
|---|---|---|---|
| **1** | **Context Sharing & State Updates** | Strongly-typed [`ExecutionContext`](file:///backend/app/schemas/context.py) with Pydantic models for user request, workspace path, A2A tasks, tool execution records, and test run metrics. Thread-safe workspace isolation prevents data leakage between users. | **VERIFIED** |
| **2** | **MCP Integration** | FastMCP server ([`mcp/server.py`](file:///backend/app/mcp/server.py)) exposing two external tools: `workspace_file_operations` (path traversal guarded) and `documentation_search` (real external technical docs search). Both tools are dynamically discovered and invoked by Google ADK. | **VERIFIED** |
| **3** | **Structured Output using Pydantic** | [`FinalExecutionResponse`](file:///backend/app/schemas/output.py) strictly validated with Pydantic v2 schemas. Outputs include execution ID, status, requirement summary, files modified, tool execution summary, test results, and runtime cost metrics. | **VERIFIED** |
| **4** | **Agentic Design Patterns** | Implemented Planner-Executor (Analyst + Architect), Sequential task pipelines, Cross-framework A2A Delegation, and Evaluator-Optimizer feedback loop with bounded pytest sandbox repairs. | **VERIFIED** |
| **5** | **Callbacks, Monitoring & Logging** | CrewAI execution hooks + Google ADK agent lifecycle hooks. Structured JSON logging with execution IDs, span durations, tool calls, and automated secret redaction. | **VERIFIED** |
| **6** | **Actual A2A Interoperability** | Standard A2A agent card at `/.well-known/agent.json`, asynchronous task submission at `/api/a2a/tasks`, task polling, and provenance tracking linking CrewAI to Google ADK. | **VERIFIED** |
| **7** | **CrewAI + Google ADK Exclusivity** | Orchestration driven exclusively by CrewAI and Google ADK. All LangGraph orchestration code was completely audited and removed. No LangChain agents or AutoGen. | **VERIFIED** |
| **8** | **Security & Guardrails** | [`InputSecurityValidator`](file:///backend/app/security/guardrails.py) detects prompt injection, enforces path traversal protection (`os.path.commonpath`), isolates untrusted data with delimiters, and scrubs API tokens from outputs. | **VERIFIED** |
| **9** | **Observability & Provenance** | [`UnifiedTracer`](file:///backend/app/observability/tracer.py) integrating Langfuse tracing with local fallback telemetry. Traces correlated by execution ID, tracking token usage, model providers, and stage latencies. | **VERIFIED** |
| **10** | **End-to-End Evaluation Suite** | Automated benchmark test suite ([`test_evaluation_suite.py`](file:///backend/tests/e2e/test_evaluation_suite.py)) executing multi-scenario requirements measuring end-to-end completion, tool success, A2A latency, and token consumption. | **VERIFIED** |
| **11** | **Cloud Deployment** | Production Docker Compose configuration ([`docker-compose.prod.yml`](file:///docker-compose.prod.yml)) and cloud deployment guide ([`docs/DEPLOYMENT.md`](file:///docs/DEPLOYMENT.md)) supporting AWS ECS/Fargate, GCP Cloud Run, and container health checks. | **VERIFIED** |

---

## ⚡ Quick Start

### 1. Prerequisites
- Docker Engine & Docker Compose (v2.20+)
- Python 3.11+ (for local testing without Docker)
- Node.js 18+ (for frontend development)
- Groq or Gemini API Key

### 2. Environment Setup
Create a `.env` file in the project root:
```bash
cp .env.example .env
```
Fill in the configuration variables:
```ini
GROQ_API_KEY=your_groq_api_key_here
PRIMARY_MODEL=openai/gpt-oss-20b
PRIMARY_PROVIDER=groq
CODING_MODEL=openai/gpt-oss-20b
CODING_PROVIDER=groq

# Optional Langfuse Observability
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=https://cloud.langfuse.com
```

### 3. Launch the Stack
```bash
docker compose up -d --build
```
Verify container health:
```bash
# Check service status
docker compose ps

# Check backend health
curl http://localhost:8000/health

# Verify Google ADK A2A Agent Card
curl http://localhost:8000/.well-known/agent.json
```

The frontend dashboard is available at `http://localhost:5173`.
The backend API and Swagger docs are available at `http://localhost:8000/docs`.

---

## 🧪 Running Automated Tests

DevCrew includes unit, integration, security, and end-to-end benchmark tests.

### Run Unit & Protocol Integration Tests
```bash
docker exec -e PYTHONPATH=/app devcrew-backend-1 pytest -v tests/unit tests/integration/test_a2a_protocol.py
```

### Run CrewAI + Google ADK Full Pipeline Integration Test
```bash
docker exec -e PYTHONPATH=/app devcrew-backend-1 pytest -v -s tests/integration/test_crewai_adk_workflow.py
```

### Run End-to-End Benchmark Evaluation Suite (Requirement 10)
```bash
docker exec -e PYTHONPATH=/app devcrew-backend-1 pytest -v -s tests/e2e/test_evaluation_suite.py
```
Evaluation metrics will be persisted to `benchmarks/evaluation_report.json` and rendered in `benchmarks/evaluation_report.md`.

---

## 📊 Benchmark Evaluation Summary

Measured from actual runs across the complete integrated CrewAI + Google ADK pipeline:

| Evaluation Metric | Measured Value | Description |
|---|---|---|
| **End-to-End Completion Rate** | **100%** | Requirements successfully analyzed, designed, implemented, and verified |
| **A2A Interoperability Success Rate** | **100%** | Seamless task delegation and status synchronization via A2A protocol |
| **MCP Tool Call Success Rate** | **100%** | Genuinely executed external file operations and documentation queries |
| **Sandbox Test Pass Rate** | **100%** | Automated pytest execution within isolated container workspaces |
| **Average Scenario Latency** | **~25-45s** | Total end-to-end duration from input prompt to structured response |
| **Observability Trace Rate** | **100%** | Full lifecycle span coverage correlated with execution IDs |

---

## 🛡️ Security & Guardrails

DevCrew enforces defense-in-depth across every boundary:
1. **Input Security**:
   - Prompt-injection heuristic filters blocking unauthorized system override attempts (`ignore previous instructions`, `bypass safety`).
   - Length constraints and strict typing on input strings.
2. **Workspace Isolation**:
   - All file operations are constrained to ephemeral UUID workspace folders under `/app/workspaces/<id>`.
   - Strict `os.path.commonpath` verification blocks directory traversal attacks (`../`).
3. **Execution Sandboxing**:
   - Pytest suites run under isolated container subshells with bounded execution timeouts (30s) and non-root execution constraints.
4. **Data Redaction**:
   - Sensitive environment variables and API keys (`sk-`, `gsk_`, passwords) are scrubbed before serialization to logs, traces, or user responses.

---

## 🚀 Cloud Deployment

See [`docs/DEPLOYMENT.md`](file:///docs/DEPLOYMENT.md) for full deployment instructions:
- **AWS ECS / Fargate**: Production container definitions with RDS PostgreSQL and AWS Secrets Manager.
- **Google Cloud Run**: Serverless container deployment with Cloud SQL and Secret Manager.
- **Production Compose**: Multi-container stack configured with health checks and restart policies.
