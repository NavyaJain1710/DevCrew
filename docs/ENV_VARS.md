# DevCrew — Environment Variable Reference

This document details all configuration options supported by the **DevCrew** backend, multi-agent frameworks, RAG engine, MCP tools, and observability layer.

---

## Configuration Variables Matrix

| Variable Name | Required | Default Value | Description |
| :--- | :--- | :--- | :--- |
| `POSTGRES_USER` | Yes | `postgres` | PostgreSQL database username |
| `POSTGRES_PASSWORD` | Yes | `postgres` | PostgreSQL database password |
| `POSTGRES_DB` | Yes | `devcrew` | Database name |
| `POSTGRES_HOST` | Yes | `db` | Database host (or `localhost` for local run) |
| `POSTGRES_PORT` | Yes | `5432` | PostgreSQL port |
| `DATABASE_URL` | No | Auto-constructed | Full asyncpg database connection string |
| `JWT_SECRET_KEY` | Yes | *Required string* | HMAC secret used for signing JWT access tokens |
| `JWT_ALGORITHM` | No | `HS256` | JWT signing algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | `1440` | JWT expiration time (24 hours) |
| `GROQ_API_KEY` | Conditional | *Empty* | API key for Groq Cloud inference |
| `OPENROUTER_API_KEY` | Conditional | *Empty* | API key for OpenRouter inference |
| `OPENAI_API_KEY` | Conditional | *Empty* | API key for OpenAI direct access |
| `GEMINI_API_KEY` | Conditional | *Empty* | API key for Google Gemini access |
| `PRIMARY_MODEL` | Yes | `openai/gpt-oss-20b` | LLM model for CrewAI planning and analysis |
| `PRIMARY_PROVIDER` | Yes | `groq` | Provider for primary model (`groq`, `openrouter`, `openai`) |
| `CODING_MODEL` | Yes | `openai/gpt-oss-20b` | LLM model for Google ADK code generation |
| `CODING_PROVIDER` | Yes | `groq` | Provider for coding model (`groq`, `openrouter`, `openai`) |
| `CHROMA_PERSIST_DIR` | No | `/app/chroma_db` | Persistent filesystem path for ChromaDB vector store |
| `WORKSPACE_BASE_DIR` | No | `/app/workspaces` | Base path for isolated project workspaces |
| `LANGFUSE_PUBLIC_KEY` | No | *Empty* | Langfuse public project key |
| `LANGFUSE_SECRET_KEY` | No | *Empty* | Langfuse secret project key |
| `LANGFUSE_HOST` | No | `https://cloud.langfuse.com` | Langfuse instance URL |
| `LOG_LEVEL` | No | `INFO` | Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |
| `A2A_TIMEOUT_SECONDS` | No | `300` | Timeout in seconds for remote A2A task executions |
| `MAX_AUTO_REPAIR_ATTEMPTS` | No | `3` | Maximum bounded test repair attempts for Google ADK |

---

## Security Best Practices
1. **Never Commit Secrets**: Never commit `.env` or files containing plain-text keys to version control.
2. **Key Rotation**: Rotate `JWT_SECRET_KEY` and LLM provider keys periodically.
3. **Secret Redaction**: DevCrew automatically redacts known key patterns (`sk-`, `gsk_`, passwords) from application logs, traces, and responses.

