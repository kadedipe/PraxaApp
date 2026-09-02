import pytest
from langchain_core.documents import Document

from praxa_rag import build_sources, validate_question


def test_validate_question_normalizes_whitespace():
    assert validate_question("  What   is Hamilton? ", 100) == "What is Hamilton?"


def test_validate_question_rejects_empty_and_oversized_input():
    with pytest.raises(ValueError, match="enter a question"):
        validate_question("   ", 100)
    with pytest.raises(ValueError, match="10 characters"):
        validate_question("x" * 11, 10)


def test_build_sources_deduplicates_and_converts_zero_based_pages():
    documents = [
        Document(page_content=" First excerpt ", metadata={"source": "/tmp/show.pdf", "page": 0}),
        Document(page_content="Duplicate", metadata={"source": "/tmp/show.pdf", "page": 0}),
    ]
    sources = build_sources(documents)
    assert len(sources) == 1
    assert sources[0].name == "show.pdf"
    assert sources[0].page == 1
