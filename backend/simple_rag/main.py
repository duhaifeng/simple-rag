"""FastAPI application entry point."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from simple_rag.api.query import router as query_router
from simple_rag.api.control_plane import router as control_plane_router
from simple_rag.config.settings import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle."""
    settings = get_settings()
    # TODO: init DB engine, load profiles, pre-warm models (lazy)
    yield
    # TODO: cleanup


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="SimpleRAG",
        version="0.1.0",
        description="Configurable RAG system with pluggable Embedding, VectorStore, BM25, Rerank.",
        lifespan=lifespan,
    )

    # CORS — allow Vue 3 dev server
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(query_router, prefix="/api/v1", tags=["query"])
    app.include_router(control_plane_router, prefix="/api/v1", tags=["control-plane"])

    return app


app = create_app()
