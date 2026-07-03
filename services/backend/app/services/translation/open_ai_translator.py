from app.services.translation.base import TranslationContext, TranslationError, TranslationResult


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
    
    def get_api_key(self) -> str:
        return self._api_key
    
    def get_model(self) -> str:
        return self._model