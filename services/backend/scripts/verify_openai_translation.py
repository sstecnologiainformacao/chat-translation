import asyncio

from app.services.translation.base import TranslationContext
from app.services.translation.factory import create_translation_provider


async def main() -> None:
    provider = create_translation_provider()

    context = TranslationContext(context="", messages=[])

    result = await provider.translate(
        text="Olá, tudo bem?",
        source_language="Portuguese",
        target_languages={"English"},
        context=context,
    )

    print(type(provider).__name__)
    print(sorted(result.translations.keys()))

    if result.context_update is None:
        return

    print(len(result.context_update.summary))
    print(len(result.context_update.entities))
    print(len(result.context_update.glossary))


if __name__ == "__main__":
    asyncio.run(main())
