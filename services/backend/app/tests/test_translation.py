from app.services.translation.base import FakeTranslator, TranslationProvider


async def test_translation() -> None:
    translator: TranslationProvider = FakeTranslator()

    result = await translator.translate(
        text="hello",
        source_language="Portuguese",
        target_language="English",
    )

    assert result == "Portuguese -> English + hello"