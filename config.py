"""Validated runtime configuration for PraxaApp."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _positive_int(name: str, default: int) -> int:
    raw = os.getenv(name, str(default))
    try:
        value = int(raw)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer") from exc
    if value < 1:
        raise ValueError(f"{name} must be greater than zero")
    return value


@dataclass(frozen=True)
class Settings:
    openrouter_api_key: str
    model_name: str
    fallback_model_name: str | None
    vector_store_path: Path
    context_data_path: Path
    retrieval_k: int
    request_timeout_seconds: int
    max_question_chars: int
    requests_per_minute: int

    @classmethod
    def from_env(cls, *, require_api_key: bool = True) -> Settings:
        key = os.getenv("OPENROUTER_API_KEY", "").strip()
        if require_api_key and not key:
            raise ValueError("OPENROUTER_API_KEY is required")
        fallback = os.getenv("OPENROUTER_FALLBACK_MODEL", "").strip() or None
        return cls(
            openrouter_api_key=key,
            model_name=os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini").strip(),
            fallback_model_name=fallback,
            vector_store_path=Path(os.getenv("VECTOR_STORE_PATH", "/app/data/chromadb")),
            context_data_path=Path(os.getenv("CONTEXT_DATA_PATH", "/app/data/context")),
            retrieval_k=_positive_int("RETRIEVAL_K", 5),
            request_timeout_seconds=_positive_int("REQUEST_TIMEOUT_SECONDS", 45),
            max_question_chars=_positive_int("MAX_QUESTION_CHARS", 2_000),
            requests_per_minute=_positive_int("REQUESTS_PER_MINUTE", 12),
        )
