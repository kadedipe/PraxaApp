from pathlib import Path

import pytest

from config import Settings


def test_settings_have_production_safe_defaults(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.delenv("OPENROUTER_MODEL", raising=False)
    settings = Settings.from_env()
    assert settings.model_name == "openai/gpt-4o-mini"
    assert settings.vector_store_path == Path("/app/data/chromadb")
    assert settings.requests_per_minute == 12


def test_api_key_is_required(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    with pytest.raises(ValueError, match="OPENROUTER_API_KEY"):
        Settings.from_env()


def test_numeric_settings_must_be_positive(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setenv("RETRIEVAL_K", "0")
    with pytest.raises(ValueError, match="greater than zero"):
        Settings.from_env()
