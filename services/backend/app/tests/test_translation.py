import pytest

from app.core.config import get_settings
from app.services.translation.base import (
    TranslationContext,
    TranslationError,
    TranslationProvider,
    TranslationResult,
)
from app.services.translation.factory import create_translation_provider
from app.services.translation.fake_translator import FakeTranslator
from app.services.translation.open_ai_translator import OpenAITranslator


async def test_translation_returns_fake_translator() -> None:
    translator: TranslationProvider = create_translation_provider()
    assert isinstance(translator, FakeTranslator)


async def test_translation_fake_translator() -> None:
    translator: TranslationProvider = FakeTranslator()
    context: TranslationContext = TranslationContext(context="", messages=[])

    result: TranslationResult = await translator.translate(
        text="hello",
        source_language="Portuguese",
        target_languages=set(["English"]),
        context=context,
    )

    assert result.translations == {
        "English": "Portuguese -> English + hello"
    }
    
async def test_open_ai_translation_check_values() -> None:
    open_ai_translation = OpenAITranslator(api_key="the-key", model="the-model")

    assert open_ai_translation.get_api_key() == "the-key"
    assert open_ai_translation.get_model() == "the-model"


async def test_return_fake_translator_if_development() -> None:
    translator: TranslationProvider = create_translation_provider()

    assert isinstance(translator, FakeTranslator)


async def test_return_open_ai_translator_if_not_development(
        monkeypatch: pytest.MonkeyPatch
    ) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-fake-test")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-5.4-fake")
    monkeypatch.setenv("IS_DEVELOPMENT", "False")
    get_settings.cache_clear()

    translator: TranslationProvider = create_translation_provider()

    assert isinstance(translator, OpenAITranslator)
    assert translator._api_key == "sk-fake-test"
    assert translator._model == "gpt-5.4-fake"


async def test_raise_translation_error_translator_not_implemented(
        monkeypatch: pytest.MonkeyPatch
    ) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-fake-test")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-5.4-fake")
    monkeypatch.setenv("IS_DEVELOPMENT", "False")
    get_settings.cache_clear()

    translator: TranslationProvider = create_translation_provider()

    with pytest.raises(TranslationError):
        await translator.translate(
            text="Test",
            source_language="Portuguese",
            target_languages=set(["English"]),
            context=TranslationContext(
                context="The context",
                messages=[]
            )
        )