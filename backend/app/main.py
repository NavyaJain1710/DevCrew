"""
FastAPI Application — DevCrew Backend

This is the application factory. All routes, middleware, and lifespan
events are registered here.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.config import get_settings
from app.database.base import create_tables
from app.services.ws_hub import ws_hub

logger = structlog.get_logger(__name__)
settings = get_settings()

import os
# Ensure CrewAI has an OPENAI_API_KEY in environment so it doesn't fail import
if not os.environ.get("OPENAI_API_KEY"):
    os.environ["OPENAI_API_KEY"] = settings.groq_api_key or os.getenv("GROQ_API_KEY") or "gsk_dummy_key_for_groq"


# ── Lifespan ──────────────────────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    logger.info("devcrew_backend_starting", env=settings.app_env)

    # Ensure workspace directory exists
    import os
    os.makedirs(settings.workspace_base_path, exist_ok=True)

    # Auto-create tables on startup (with safety timeout)
    try:
        import asyncio
        await asyncio.wait_for(create_tables(), timeout=10.0)
        logger.info("database_tables_initialized")
    except Exception as e:
        logger.warning("db_init_warning", error=str(e))

    logger.info("devcrew_backend_ready", port=settings.app_port)
    yield
    logger.info("devcrew_backend_stopping")


# ── Application factory ────────────────────────────────────────────────────────


def create_app() -> FastAPI:
    app = FastAPI(
        title="DevCrew API",
        description=(
            "DevCrew — Autonomous Multi-Agent AI Software Development Team.\n\n"
            "A multi-agent system that transforms natural-language requirements into "
            "tested, reviewed, and documented software projects."
        ),
        version="1.0.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
        lifespan=lifespan,
    )

    # ── Middleware ─────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # ── API Routers ────────────────────────────────────────────────────────
    from app.api.auth import router as auth_router
    from app.api.projects import router as projects_router
    from app.api.agents import router as agents_router
    from app.api.files import router as files_router
    from app.api.reports import router as reports_router
    from app.api.admin import router as admin_router
    from app.api.documents import router as documents_router
    from app.api.mcp_routes import router as mcp_router
    from app.a2a.server import router as a2a_router

    app.include_router(auth_router, prefix="/api")
    app.include_router(projects_router, prefix="/api")
    app.include_router(documents_router, prefix="/api")
    app.include_router(mcp_router, prefix="/api")
    app.include_router(agents_router, prefix="/api")
    app.include_router(files_router, prefix="/api")
    app.include_router(reports_router, prefix="/api")
    app.include_router(admin_router, prefix="/api")
    app.include_router(a2a_router)

    # ── WebSocket ──────────────────────────────────────────────────────────
    @app.websocket("/ws/{project_id}")
    async def websocket_endpoint(ws: WebSocket, project_id: str):
        """
        WebSocket endpoint for real-time project updates.
        Connect with: ws://localhost:8000/ws/{project_id}
        Pass JWT token as query param: ?token=...
        """
        # Basic token validation
        token = ws.query_params.get("token", "")
        if not token:
            await ws.close(code=4001, reason="Authentication required")
            return

        try:
            from jose import jwt
            payload = jwt.decode(
                token, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
            )
            user_id = payload.get("sub")
            if not user_id:
                await ws.close(code=4001, reason="Invalid token")
                return
        except Exception:
            await ws.close(code=4001, reason="Invalid token")
            return

        await ws_hub.connect(project_id, ws)
        logger.info("ws_client_connected", project_id=project_id, user_id=user_id)

        try:
            while True:
                # Keep connection alive, handle ping/pong
                data = await ws.receive_text()
                if data == "ping":
                    await ws.send_text("pong")
        except WebSocketDisconnect:
            await ws_hub.disconnect(project_id, ws)
            logger.info("ws_client_disconnected", project_id=project_id)

    # ── Root & Health Check ────────────────────────────────────────────────
    @app.get("/", tags=["Root"])
    async def root():
        return {
            "name": "DevCrew Multi-Agent Platform API",
            "status": "online",
            "version": "1.0.0",
            "documentation": "/api/docs",
            "agent_card": "/.well-known/agent.json",
            "mcp_tools": "/api/mcp/tools",
            "frontend": "http://localhost:5173",
        }

    @app.get("/docs", include_in_schema=False)
    async def docs_redirect():
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/api/docs")

    @app.get("/health", tags=["Health"])
    @app.get("/api/health", tags=["Health"])
    async def health_check():
        return {
            "status": "healthy",
            "service": "devcrew-backend",
            "version": "1.0.0",
            "env": settings.app_env,
        }

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.app_env == "development",
        log_level="info",
    )
