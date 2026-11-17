# DevCrew — Verification & Testing Guide

This document describes the automated test suites, testing methodologies, and reproducible commands used to verify all components of **DevCrew**.

---

## 1. Test Suite Architecture

The test suite is organized into three distinct tiers:

1. **Unit Tests (`tests/unit/`)**: Fast, deterministic tests verifying individual services, Pydantic schemas, security guardrails, text chunking, document extractors, and MCP tool functions.
2. **Integration Tests (`tests/integration/`)**: Tests verifying cross-service communication, including the A2A protocol, Agent Card discovery, dynamic RAG and MCP endpoints, and the complete CrewAI + Google ADK workflow.
3. **End-to-End Evaluation Suite (`tests/e2e/`)**: Multi-scenario autonomous software development benchmarks verifying live LLM calls, tool execution, test execution, and the Evaluator-Optimizer auto-repair loop.

---

## 2. Running Tests Inside Docker

### 2.1 Run Unit Tests (20 Tests)
```bash
docker exec -e PYTHONPATH=/app devcrew-backend-1 pytest tests/unit/ -v
```
*Expected Result*: All 20 tests pass.
*Coverage*:
- `test_document_extractor_pdf`
- `test_document_extractor_docx`
- `test_document_extractor_code`
- `test_text_chunker`
- `test_dynamic_rag_indexing`
- `test_dynamic_rag_retrieval`
- `test_dynamic_rag_empty_state_handling`
- `test_dynamic_rag_updates_and_deletions`
- `test_multi_user_isolation`
- `test_mcp_tool_discovery`
- `test_mcp_workspace_file_operations`
- `test_mcp_documentation_search`
- `test_execution_context_defaults`
- `test_execution_context_record_tool_call`
- `test_final_execution_response_markdown`
- `test_input_sanitization_valid`
- `test_input_too_short`
- `test_prompt_injection_detection`
- `test_secret_redaction`
- `test_path_traversal_prevention`

### 2.2 Run Integration Tests (5 Tests)
```bash
docker exec -e PYTHONPATH=/app devcrew-backend-1 pytest tests/integration/ -v
```
*Expected Result*: All 5 tests pass.
*Coverage*:
- `test_a2a_agent_card_discovery`
- `test_a2a_task_submission_and_lifecycle`
- `test_full_crewai_adk_pipeline`
- `test_api_mcp_discovery_and_execution`
- `test_api_document_lifecycle`

### 2.3 Run End-to-End Evaluation Benchmark Suite (Requirement 10)
```bash
docker exec -e PYTHONPATH=/app devcrew-backend-1 pytest tests/e2e/test_evaluation_suite.py -v
```
*Expected Result*: 100% scenario pass rate.
*What it tests*:
- Autonomous execution across 4 distinct software engineering scenarios.
- Real LLM calls with rate limit handling and bounded retries.
- Real MCP tool execution (`workspace_file_operations`, `documentation_search`).
- Real `pytest` test runner execution in sandboxed workspaces.
- Real Google ADK Evaluator-Optimizer auto-repair on failing test suites.
- Structured evaluation metrics saved to `benchmarks/evaluation_report.json`.

---

## 3. Frontend Verification
To verify the frontend TypeScript build:
```bash
cd frontend
npm run build
```
*Expected Result*: `tsc -b && vite build` succeeds with 0 errors.

