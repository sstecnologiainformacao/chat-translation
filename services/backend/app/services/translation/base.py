from typing import Protocol


class TranslationError(Exception):
    "Raise an exception when we have an error during the translation process"


class TranslationProvider(Protocol):
    async def translate(self, *, text: str, source_language: str, target_language: list[str]) -> str:
        ...


class FakeTranslator:

    async def translate(self, *, text: str, source_language: str, target_language: list[str]) -> str:
        languages = "".join(target_language)
        return f"{source_language} -> {languages} + {text}"
    
