import pytest
from langchain_core.documents import Document

from praxa_rag import Source, build_sources, is_valid_grounded_answer, validate_question


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


def test_grounded_answer_quality_gate_rejects_metadata_and_missing_citations():
    sources = [Source(citation=1, name="shows.pdf", page=3, excerpt="Evidence")]
    assert is_valid_grounded_answer("Retrograde opens at the Apollo [1].", sources)
    assert not is_valid_grounded_answer("User Safety: safe", sources)
    assert not is_valid_grounded_answer("Retrograde opens at the Apollo.", sources)


def test_grounded_answer_quality_gate_allows_explicit_abstention():
    sources = [Source(citation=1, name="shows.pdf", page=3, excerpt="Evidence")]
    assert is_valid_grounded_answer(
        "I could not find this in the theatre sources.", sources
    )
