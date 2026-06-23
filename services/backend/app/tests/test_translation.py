from app.services.translation.base import (
    FakeTranslator,
    TranslationContext,
    TranslationProvider,
    TranslationResult,
)


async def test_translation() -> None:
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