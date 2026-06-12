from typing import Protocol


class TranslationError(Exception):
    "Raise an exception when we have an error during the translation process"


class TranslationProvider(Protocol):
    async def translate(self, *, text: str, source_language: str, target_language: str) -> str:
        ...


class FakeTranslator:

    async def translate(self, *, text: str, source_language: str, target_language: str) -> str:
        return f"{source_language} -> {target_language} + {text}"