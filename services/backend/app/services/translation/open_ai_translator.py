from app.services.translation.base import (
    Message,
    TranslationClient,
    TranslationContext,
    TranslationContextUpdate,
    TranslationError,
    TranslationResult,
)


class OpenAITranslator:
    def __init__(self, *, api_key: str, model: str, client: TranslationClient | None = None):
        self._api_key = api_key
        self._model = model
        self._client = client

    async def translate(
        self,
        *,
        text: str,
        source_language: str,
        target_languages: set[str],
        context: TranslationContext,
    ) -> TranslationResult:

        api_parameters = self._build_api_parameters(
            text=text,
            source_language=source_language,
            target_languages=target_languages,
            context=context,
        )
        if self._client is None:
            raise TranslationError()

        response = await self._client.translate(api_parameters=api_parameters)
        return self._parse_open_ai_response(response=response)

    def _build_api_parameters(
        self,
        *,
        text: str,
        source_language: str,
        target_languages: set[str],
        context: TranslationContext,
    ) -> dict[str, object]:

        return {
            "model": self._model,
            "reasoning": {"effort": "low"},
            "instructions": (
                "You're a great translator. "
                'You need to translate the text present on the attribute "input" '
                "and that was wrote in "
                f"{source_language} to {', '.join(sorted(target_languages))}. "
                f'Translate the text using this context "{context.context}", '
                "and the last messages: "
                f"{self.get_list_messages_as_text(messages=context.messages)}"
            ),
            "input": text,
        }

    def _parse_open_ai_response(self, *, response: dict[str, object]) -> TranslationResult:
        translations_raw = response.get("translations")
        context_update_raw = response.get("context_update")

        if translations_raw is None or context_update_raw is None:
            raise TranslationError()

        if isinstance(translations_raw, dict) and isinstance(context_update_raw, dict):
            summary_raw = context_update_raw.get("summary")
            tone_raw = context_update_raw.get("tone")
            entities_raw = context_update_raw.get("entities")
            glossary_raw = context_update_raw.get("glossary")

            if not isinstance(summary_raw, str):
                raise TranslationError()

            if not isinstance(tone_raw, str):
                raise TranslationError()

            if not isinstance(entities_raw, list):
                raise TranslationError()

            if not isinstance(glossary_raw, dict):
                raise TranslationError()

            new_context: TranslationContextUpdate = TranslationContextUpdate(
                summary=summary_raw, tone=tone_raw, entities=entities_raw, glossary=glossary_raw
            )
            return TranslationResult(translations=translations_raw, context_update=new_context)

        raise TranslationError()

    def get_list_messages_as_text(self, *, messages: list[Message]) -> str:
        list_messages: list[str] = list()
        for message in messages:
            list_messages.append(f"nickname: {message.nickname}, message: {message.message};")

        return "".join(list_messages)

    def get_api_key(self) -> str:
        return self._api_key

    def get_model(self) -> str:
        return self._model
