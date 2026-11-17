# DevCrew Cloud Deployment & Operations Guide

This guide details the production deployment, networking, security, observability, and rollback procedures for **DevCrew** (Multi-Agent Software Engineering Platform utilizing **CrewAI + Google ADK** over the **A2A Protocol** and **MCP**).

---

## 1. Architectural Overview

DevCrew deploys as a microservices architecture comprising:
1. **Frontend Service**: React 18 + Vite (SPA) serving the orchestration dashboard and live agent telemetry.
2. **Backend Service**: FastAPI 0.115 + Python 3.11 coordinating CrewAI agents, Google ADK agents, FastMCP server, and A2A protocol router.
3. **Database Service**: PostgreSQL 15 storing project states, requirements, architecture models, test execution metrics, security scan findings, and audit logs.
4. **Vector Database / Embedding Engine**: Sentence-Transformers + Local Vector Index / ChromaDB for architectural pattern retrieval.
5. **Observability Stack**: Integrated Langfuse tracing and local telemetry metrics.

---

## 2. Environment Variables & Secrets Reference

Configure these variables via cloud secret managers (AWS Secrets Manager, GCP Secret Manager, Azure Key Vault, or Kubernetes Secrets).

| Variable | Description | Example / Default |
|---|---|---|
| `APP_ENV` | Application environment | `production` |
| `APP_HOST` | FastAPI host bind | `0.0.0.0` |
| `APP_PORT` | FastAPI port | `8000` |
| `FRONTEND_URL` | Trusted CORS frontend origin | `https://devcrew.yourdomain.com` |
| `JWT_SECRET` | Cryptographic secret for auth tokens | Minimum 32-character high-entropy secret |
| `DATABASE_URL` | Async PostgreSQL connection string | `postgresql+asyncpg://user:pass@host:5432/devcrew` |
| `DATABASE_URL_SYNC` | Sync PostgreSQL connection string | `postgresql://user:pass@host:5432/devcrew` |
| `GROQ_API_KEY` | Groq API key for low-latency inference | `gsk_...` |
| `OPENROUTER_API_KEY` | OpenRouter API key (fallback provider) | `sk-or-...` |
| `GEMINI_API_KEY` | Google Gemini API key (optional) | `AIza...` |
| `PRIMARY_MODEL` | Reasoning & architecture model | `openai/gpt-oss-20b` |
| `PRIMARY_PROVIDER` | Provider for primary reasoning tier | `groq` |
| `CODING_MODEL` | Code implementation & repair model | `openai/gpt-oss-20b` |
| `CODING_PROVIDER` | Provider for code synthesis tier | `groq` |
| `LANGFUSE_PUBLIC_KEY` | Observability public key | `pk-lf-...` |
| `LANGFUSE_SECRET_KEY` | Observability secret key | `sk-lf-...` |
| `LANGFUSE_HOST` | Langfuse telemetry endpoint | `https://cloud.langfuse.com` |

---

## 3. Production Deployment with Docker Compose

### Prerequisites
- Docker Engine >= 24.0
- Docker Compose v2 >= 2.20

### Start Production Stack
```bash
# 1. Clone repository
git clone https://github.com/your-org/DevCrew.git
cd DevCrew

# 2. Provision environment configuration
cp .env.example .env
# Edit .env with production credentials

# 3. Build and launch services
docker compose -f docker-compose.prod.yml up -d --build

# 4. Verify service health
docker compose -f docker-compose.prod.yml ps
```

---

## 4. Kubernetes / Cloud Deployment (AWS ECS / GCP Cloud Run)

### Google Cloud Run Deployment
DevCrew's modular architecture can be deployed to Google Cloud Run:
```bash
# 1. Submit backend image build to Google Artifact Registry
gcloud builds submit --tag gcr.io/$PROJECT_ID/devcrew-backend:latest ./backend

# 2. Deploy backend service to Cloud Run
gcloud run deploy devcrew-backend \
  --image gcr.io/$PROJECT_ID/devcrew-backend:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars APP_ENV=production,PRIMARY_PROVIDER=groq \
  --set-secrets GROQ_API_KEY=devcrew-groq-key:latest,DATABASE_URL=devcrew-db-url:latest
```

---

## 5. Health Checks & Monitoring Endpoints

- **System Health**: `GET /api/health`
  - Validates PostgreSQL connectivity, workspace write accessibility, and provider routing.
- **A2A Agent Card Discovery**: `GET /.well-known/agent.json`
  - Complies with official A2A protocol specifications.
- **Prometheus Metrics**: `GET /metrics`
  - Emits latency histograms, stage durations, and agent invocation counters.

---

## 6. Rollback & Disaster Recovery Procedures

### Rolling Back Docker Compose
```bash
# Revert to previous image tag or Git commit
git checkout HEAD~1
docker compose -f docker-compose.prod.yml up -d --build
```

### Database Migration Rollback
```bash
# Roll back one Alembic migration step
docker exec devcrew-backend-1 alembic downgrade -1
```
