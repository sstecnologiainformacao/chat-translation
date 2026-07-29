from pydantic import ValidationError

from app.services.translation.base import (
    Message,
    TranslationClient,
    TranslationContext,
    TranslationContextUpdate,
    TranslationError,
    TranslationResult,
)
from app.services.translation.open_ai_models import OpenAITranslationResponse


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
                "Return translations for each target language and update the translation context"
                " as context_update with summary, tone, entities, and glossary. "
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
        try:
            parsed_response = OpenAITranslationResponse.model_validate(response)
        except ValidationError as error:
            raise TranslationError() from error

        glossary_item = {}
        for glossary in parsed_response.context_update.glossary:
            glossary_item[glossary.term] = glossary.translation

        context_response = TranslationContextUpdate(
            summary=parsed_response.context_update.summary,
            tone=parsed_response.context_update.tone,
            entities=parsed_response.context_update.entities,
            glossary=glossary_item,
        )

        translation_items = {}
        for item in parsed_response.translations:
            translation_items[item.language] = item.text

        return TranslationResult(
            translations=translation_items,
            context_update=context_response,
        )

    def get_list_messages_as_text(self, *, messages: list[Message]) -> str:
        list_messages: list[str] = list()
        for message in messages:
            list_messages.append(f"nickname: {message.nickname}, message: {message.message};")

        return "".join(list_messages)

    def get_api_key(self) -> str:
        return self._api_key

    def get_model(self) -> str:
        return self._model
