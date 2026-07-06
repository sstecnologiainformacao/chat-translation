from app.services.translation.base import (
    Message,
    TranslationContext,
    TranslationError,
    TranslationResult,
)


class OpenAITranslator:
    def __init__(self, *, api_key: str, model: str):
        self._api_key = api_key
        self._model = model
        
    async def translate(
        self,
        *,
        text: str,
        source_language: str,
        target_languages: set[str],
        context: TranslationContext
    ) -> TranslationResult:
        raise TranslationError()
    
    def _build_api_parameters(
        self,
        *,
        text: str,
        source_language: str,
        target_languages: set[str],
        context: TranslationContext
    ) -> dict[str, object]:
         
        return {
            "model": self._model,
            "reasoning": { "effort": "low" },
            "instructions": 
                (
                    'You\'re a great translator. '
                    'You need to translate the text present on the attribute "input" '
                    'and that was wrote in '
                    f'{source_language} to {", ".join(sorted(target_languages))}. '
                    f'Translate the text using this context "{context.context}", '
                    'and the last messages: '
                    f'{self.get_list_messages_as_text(messages=context.messages)}'
                ),
            "input": text,
        }
    
    def get_list_messages_as_text(self, *, messages: list[Message]) -> str:
        list_messages: list[str] = list()
        for message in messages:
            list_messages.append(f'nickname: {message.nickname}, message: {message.message};')

        return "".join(list_messages)
    
    def get_api_key(self) -> str:
        return self._api_key
    
    def get_model(self) -> str:
        return self._model