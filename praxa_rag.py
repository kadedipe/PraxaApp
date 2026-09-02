"""Grounded retrieval-augmented generation service."""

from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass
from pathlib import Path

from langchain_core.documents import Document
from langchain_core.messages import HumanMessage, SystemMessage

import context
from config import Settings
from praxa_model import SYSTEM_PROMPT, get_model

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Source:
    citation: int
    name: str
    page: int | str
    excerpt: str


def validate_question(question: str, max_chars: int) -> str:
    cleaned = re.sub(r"\s+", " ", question).strip()
    if not cleaned:
        raise ValueError("Please enter a question.")
    if len(cleaned) > max_chars:
        raise ValueError(f"Question must be {max_chars:,} characters or fewer.")
    return cleaned


def build_sources(documents: list[Document]) -> list[Source]:
    sources: list[Source] = []
    seen: set[tuple[str, object]] = set()
    for document in documents:
        raw_page = document.metadata.get("page", "unknown")
        page = raw_page + 1 if isinstance(raw_page, int) else raw_page
        name = Path(str(document.metadata.get("source") or "Theatre source")).name.replace("_", " ")
        key = (name, page)
        if key in seen:
            continue
        seen.add(key)
        sources.append(
            Source(
                len(sources) + 1,
                name,
                page,
                re.sub(r"\s+", " ", document.page_content).strip()[:500],
            )
        )
    return sources


class PraxaRAG:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or Settings.from_env()
        self.vector_store = context.get_or_create_vector_store(
            self.settings.context_data_path, self.settings.vector_store_path
        )

    def _invoke(self, messages: list[object]):
        try:
            return get_model(self.settings).invoke(messages)
        except Exception:
            if not self.settings.fallback_model_name:
                raise
            logger.warning("primary_model_failed_using_fallback", exc_info=True)
            return get_model(self.settings, self.settings.fallback_model_name).invoke(messages)

    def search_sources(self, query: str, limit: int = 5) -> list[Source]:
        """Return page-level evidence without invoking the language model."""
        query = validate_question(query, self.settings.max_question_chars)
        limit = max(1, min(limit, 10))
        documents = self.vector_store.similarity_search(query, k=limit)
        return build_sources(documents)

    def answer_and_sources(self, question: str) -> dict[str, object]:
        started = time.perf_counter()
        question = validate_question(question, self.settings.max_question_chars)
        documents = self.vector_store.similarity_search(question, k=self.settings.retrieval_k)
        sources = build_sources(documents)
        if not sources:
            return {
                "answer": "I could not find this in the theatre sources.",
                "sources": [],
                "latency_ms": 0,
            }
        excerpts = "\n\n".join(f"[{i}] {doc.page_content}" for i, doc in enumerate(documents, 1))
        response = self._invoke(
            [
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(content=f"Question: {question}\n\nExcerpts:\n{excerpts}"),
            ]
        )
        answer = getattr(response, "content", str(response)).strip()
        latency_ms = round((time.perf_counter() - started) * 1000)
        logger.info(
            "rag_request_complete", extra={"latency_ms": latency_ms, "sources": len(sources)}
        )
        return {"answer": answer, "sources": sources, "latency_ms": latency_ms}


_service: PraxaRAG | None = None


def answer_and_sources(question: str) -> dict[str, object]:
    global _service
    if _service is None:
        _service = PraxaRAG()
    return _service.answer_and_sources(question)
