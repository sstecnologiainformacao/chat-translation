import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def _set_test_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Provide test values for required env vars before Settings is instantiated."""
    monkeypatch.setenv("CHAT_USER", "test-user")
    monkeypatch.setenv("CHAT_PASSWORD", "test-pass")
    monkeypatch.setenv("JWT_SECRET", "a" * 64)
    monkeypatch.setenv("JWT_EXPIRES_MINUTES", "60")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-5.4-mini")
    # Reset the cached Settings between tests
    from app.core.config import get_settings

    get_settings.cache_clear()


@pytest.fixture
def app() -> FastAPI:
    from app.main import create_app

    return create_app()


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    return TestClient(app)
