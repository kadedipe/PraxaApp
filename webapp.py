"""Production HTTP API and single-page WebMCP interface for Praxa."""

from __future__ import annotations

import asyncio
from dataclasses import asdict
from functools import lru_cache
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from praxa_rag import PraxaRAG

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(
    title="Praxa Theatre Research API",
    description="Grounded theatre research with page-level citations and WebMCP tools.",
    version="2.0.0",
    docs_url=None,
    redoc_url=None,
)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2_000)


@lru_cache(maxsize=1)
def get_rag() -> PraxaRAG:
    return PraxaRAG()


def serialize_result(result: dict[str, object]) -> dict[str, object]:
    return {
        **result,
        "sources": [asdict(source) for source in result.get("sources", [])],
    }


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Origin-Agent-Cluster"] = "?1"
    response.headers["Permissions-Policy"] = "tools=(self)"
    return response


@app.get("/", include_in_schema=False)
async def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/healthz")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "praxa-web"}


@app.post("/api/ask")
async def ask(payload: AskRequest) -> dict[str, object]:
    try:
        result = await asyncio.to_thread(get_rag().answer_and_sources, payload.question)
        return serialize_result(result)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=503, detail="The research service is temporarily unavailable.") from exc


@app.get("/api/search")
async def search(
    q: str = Query(min_length=1, max_length=2_000),
    limit: int = Query(default=5, ge=1, le=10),
) -> dict[str, object]:
    try:
        sources = await asyncio.to_thread(get_rag().search_sources, q, limit)
        return {"query": q, "sources": [asdict(source) for source in sources]}
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=503, detail="The archive is temporarily unavailable.") from exc
