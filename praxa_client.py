"""Praxa's production Streamlit interface."""

from __future__ import annotations

import json
import logging
import time
from collections import deque
from dataclasses import asdict, is_dataclass

import streamlit as st

from config import Settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

st.set_page_config(page_title="Praxa Theater Assistant", page_icon="🎭", layout="wide")


@st.cache_resource(show_spinner="Preparing the theatre knowledge base…")
def load_rag():
    from praxa_rag import PraxaRAG

    return PraxaRAG()


def allowed_request(limit: int) -> bool:
    now = time.monotonic()
    timestamps = st.session_state.setdefault("request_times", deque())
    while timestamps and now - timestamps[0] >= 60:
        timestamps.popleft()
    if len(timestamps) >= limit:
        return False
    timestamps.append(now)
    return True


def render_sources(sources: list[object]) -> None:
    if not sources:
        return
    with st.expander(f"Verified sources ({len(sources)})"):
        for source in sources:
            item = asdict(source) if is_dataclass(source) else source
            st.markdown(f"**[{item['citation']}] {item['name']} — page {item['page']}**")
            st.caption(item["excerpt"])


settings = Settings.from_env(require_api_key=False)
st.title("🎭 Praxa Theater Assistant")
st.caption("Grounded answers about Broadway and West End theatre, with page-level sources.")

with st.sidebar:
    st.subheader("Conversation")
    if st.button("New conversation", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    history = st.session_state.get("messages", [])
    st.download_button(
        "Export conversation",
        json.dumps(history, indent=2),
        file_name="praxa-conversation.json",
        mime="application/json",
        use_container_width=True,
        disabled=not history,
    )
    st.caption("Praxa answers from its indexed sources and may still make mistakes.")

messages = st.session_state.setdefault("messages", [])
for message in messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message["role"] == "assistant":
            render_sources(message.get("sources", []))

question = st.chat_input(
    "Ask about a show, playwright, venue, or production…", max_chars=settings.max_question_chars
)
if question:
    messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    if not allowed_request(settings.requests_per_minute):
        answer = "You’ve reached the per-minute request limit. Please wait briefly and try again."
        sources = []
        latency_ms = None
    else:
        try:
            with st.spinner("Searching verified theatre sources…"):
                response = load_rag().answer_and_sources(question)
            answer = str(response["answer"])
            sources = [asdict(source) for source in response["sources"]]
            latency_ms = response.get("latency_ms")
        except ValueError as exc:
            answer, sources, latency_ms = str(exc), [], None
        except Exception:
            logging.getLogger(__name__).exception("request_failed")
            answer = "Praxa is temporarily unavailable. Please try again in a moment."
            sources, latency_ms = [], None

    with st.chat_message("assistant"):
        st.markdown(answer)
        render_sources(sources)
        if latency_ms is not None:
            st.caption(f"Answered in {latency_ms / 1000:.1f}s")
        st.feedback("thumbs", key=f"feedback_{len(messages)}")
    messages.append({"role": "assistant", "content": answer, "sources": sources})
