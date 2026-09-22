from core.config import DEFAULT_CHROMA_PERSIST_DIR, get_config


def test_defaults_when_unset(monkeypatch):
    monkeypatch.delenv("CHROMA_PERSIST_DIR", raising=False)
    monkeypatch.delenv("CHAT_MODEL_NAME", raising=False)

    config = get_config()

    assert config.chroma_persist_dir == DEFAULT_CHROMA_PERSIST_DIR
    assert config.chat_model_name is None


def test_overrides_from_env(monkeypatch):
    monkeypatch.setenv("CHROMA_PERSIST_DIR", "/tmp/custom-chroma")
    monkeypatch.setenv("CHAT_MODEL_NAME", "gemini-custom-flash")

    config = get_config()

    assert config.chroma_persist_dir == "/tmp/custom-chroma"
    assert config.chat_model_name == "gemini-custom-flash"
