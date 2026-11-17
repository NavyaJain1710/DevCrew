# DevCrew — Complete Setup & Installation Guide

This guide provides step-by-step instructions to set up, configure, and run **DevCrew** locally and in containerized environments.

---

## 1. Prerequisites

Before installing DevCrew, verify that your machine has the following tools installed:

| Requirement | Minimum Version | Recommended |
| :--- | :--- | :--- |
| **Docker Engine** | 20.10+ | 24.0+ |
| **Docker Compose** | 2.20+ | 2.28+ |
| **Node.js** | 18.0+ | 20 LTS (for local frontend dev) |
| **Python** | 3.11+ | 3.11.9 (for local backend testing) |
| **Git** | 2.30+ | Latest |

---

## 2. Clone and Configure

### 2.1 Clone Repository
```bash
git clone <repository_url>
cd DevCrew
```

### 2.2 Environment File Setup
Create your `.env` configuration file from the template:
```bash
cp .env.example .env
```

Ensure your `.env` contains valid LLM API keys:
```env
# Database
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=devcrew
POSTGRES_HOST=db
POSTGRES_PORT=5432

# Authentication
JWT_SECRET_KEY=devcrew-super-secret-jwt-key-replace-in-production-min-32-chars
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# LLM Providers (OpenRouter / Groq / OpenAI)
OPENROUTER_API_KEY=your_openrouter_api_key_here
GROQ_API_KEY=your_groq_api_key_here
PRIMARY_MODEL=openai/gpt-oss-20b
PRIMARY_PROVIDER=groq
CODING_MODEL=openai/gpt-oss-20b
CODING_PROVIDER=groq

# ChromaDB Persistent Storage
CHROMA_PERSIST_DIR=/app/chroma_db

# Observability (Optional)
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=https://cloud.langfuse.com
```

---

## 3. Starting the Platform with Docker Compose

DevCrew includes a fully containerized multi-tier stack:
- **`devcrew-frontend`**: React 18 + Vite (Port 5173)
- **`devcrew-backend`**: FastAPI + Uvicorn + ChromaDB + FastMCP (Port 8000)
- **`devcrew-db`**: PostgreSQL 15 Alpine (Port 5432)

### 3.1 Build and Launch Containers
```bash
docker compose up -d --build
```

### 3.2 Verify Container Health
```bash
docker compose ps
```
All containers should display state `Up` and `healthy`.

### 3.3 Verify Endpoints
* **Frontend Web Dashboard**: [http://localhost:5173](http://localhost:5173)
* **Backend API Root**: [http://localhost:8000](http://localhost:8000)
* **API Documentation (Swagger)**: [http://localhost:8000/docs](http://localhost:8000/docs)
* **Health Check**: [http://localhost:8000/health](http://localhost:8000/health)
* **A2A Agent Card**: [http://localhost:8000/.well-known/agent.json](http://localhost:8000/.well-known/agent.json)
* **Discovered MCP Tools**: [http://localhost:8000/api/mcp/tools](http://localhost:8000/api/mcp/tools)

---

## 4. Local Development Without Docker (Optional)

### 4.1 Backend Setup
```bash
cd backend
python -m venv venv

# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 4.2 Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
The Vite development server will start on `http://localhost:5173`.

