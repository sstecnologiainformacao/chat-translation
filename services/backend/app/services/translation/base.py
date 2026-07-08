from typing import Protocol, Self


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

    @classmethod
    def new_instance(cls) -> Self:
        return cls(context="", messages=[])


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
        self, *, translations: dict[str, str], context_update: TranslationContextUpdate | None
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
        context: TranslationContext,
    ) -> TranslationResult: ...


class TranslationClient(Protocol):
    async def translate(
        self,
        *,
        api_parameters: dict[str, object],
    ) -> dict[str, object]: ...
