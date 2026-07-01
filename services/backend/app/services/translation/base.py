from typing import Protocol


class Message:
    def __init__(self, *, message: str, nickname: str):
        self.message = message
        self.nickname = nickname


class TranslationError(Exception):
    "Raise an exception when we have an error during the translation process"


class TranslationContext:
    def __init__(self, *, context: str, messages: list[Message]):
        self.context = context
        self.messages = messages


class TranslationContextUpdate:
    def __init__(
            self,
            *,
            summary: str,
            tone: str,
            entities: list[str],
            glossary: dict[str, str],
        ):
        self.summary = summary
        self.tone = tone
        self.entities = entities
        self.glossary = glossary


class TranslationResult:
    def __init__(
            self,
            *,
            translations: dict[str, str],
            context_update: TranslationContextUpdate | None
        ):
        self.translations = translations
        self.context_update = context_update


class TranslationProvider(Protocol):
    async def translate(
            self,
            *,
            text: str,
            source_language: str,
            target_languages: set[str],
            context: TranslationContext
        ) -> TranslationResult:
        ...


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
    
