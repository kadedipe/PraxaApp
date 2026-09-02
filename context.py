"""Document ingestion and persistent retrieval infrastructure."""

from __future__ import annotations

import logging
from collections.abc import Iterable
from pathlib import Path

import gdown
from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)
DEFAULT_DOCUMENTS = (
    {
        "url": "https://quanticedu.github.io/praxa/Longest Running Shows on Broadway 2025.pdf",
        "filename": "broadway.pdf",
    },
    {
        "url": (
            "https://quanticedu.github.io/praxa/"
            "Every play and musical coming to the West End in 2025.pdf"
        ),
        "filename": "west_end.pdf",
    },
)


def download_context_data(pdfs: Iterable[dict[str, str]], path: str | Path) -> None:
    destination = Path(path)
    destination.mkdir(parents=True, exist_ok=True)
    for pdf in pdfs:
        target = destination / pdf["filename"]
        if target.exists() and target.stat().st_size > 0:
            continue
        logger.info(
            "downloading_context_document",
            extra={"document_filename": target.name},
        )
        result = gdown.download(pdf["url"], str(target), quiet=True)
        if not result or not target.exists():
            raise RuntimeError(f"Failed to download {target.name}")


def load_context_data(path: str | Path) -> list[Document]:
    docs = PyPDFDirectoryLoader(str(path)).load()
    if not docs:
        raise ValueError("No PDF documents were found in the context directory")
    return docs


def chunk_context_data(context_data: list[Document]) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=900, chunk_overlap=150, add_start_index=True
    )
    return splitter.split_documents(context_data)


def get_embedding_model() -> HuggingFaceEmbeddings:
    return HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        encode_kwargs={"normalize_embeddings": True},
    )


def get_or_create_vector_store(
    context_path: str | Path,
    vector_path: str | Path,
    embedding_model: Embeddings | None = None,
) -> Chroma:
    """Load the persistent index, bootstrapping it once when empty."""
    context_dir, vector_dir = Path(context_path), Path(vector_path)
    context_dir.mkdir(parents=True, exist_ok=True)
    vector_dir.mkdir(parents=True, exist_ok=True)
    embeddings = embedding_model or get_embedding_model()
    store = Chroma(
        persist_directory=str(vector_dir),
        embedding_function=embeddings,
        collection_name="praxa_theatre_v1",
    )
    if store.get(limit=1).get("ids"):
        return store
    download_context_data(DEFAULT_DOCUMENTS, context_dir)
    chunks = chunk_context_data(load_context_data(context_dir))
    logger.info("building_vector_index", extra={"chunks": len(chunks)})
    store.add_documents(chunks)
    return store
