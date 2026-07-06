from app.services.translation.base import (
    TranslationContext,
    TranslationContextUpdate,
    TranslationResult,
)


class FakeTranslator:

    async def translate(
        self,
        *,
        text: str,
        source_language: str,
        target_languages: set[str],
        context: TranslationContext
    ) -> TranslationResult:
        new_target_languages = set(target_languages)
        new_target_languages.discard(source_language)
        if len(new_target_languages) == 0:
            return TranslationResult(
                translations={},
                context_update=None
            )
        translations = {}
        for language in new_target_languages:
            translations[language] = f"{source_language} -> {language} + {text}"

        result = TranslationResult(
            translations=translations,
            context_update=TranslationContextUpdate(
                summary="",
                tone="",
                entities=[],
                glossary={},
            )
        )
        return result
