import praxa_model
from config import Settings


def test_get_model_excludes_reasoning(monkeypatch):
    captured = {}

    def fake_chat_openai(**kwargs):
        captured.update(kwargs)
        return object()

    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setattr(praxa_model, "ChatOpenAI", fake_chat_openai)

    praxa_model.get_model(Settings.from_env())

    assert captured["extra_body"] == {"reasoning": {"exclude": True}}
    assert captured["model"] == "openai/gpt-4o-mini"
