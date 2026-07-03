from app.core.config import Settings, get_settings
from app.services.translation.base import TranslationProvider
from app.services.translation.fake_translator import FakeTranslator
from app.services.translation.open_ai_translator import OpenAITranslator


def create_translation_provider() -> TranslationProvider:
    settings: Settings = get_settings()

    if settings.is_development:
        return FakeTranslator()
    
    return OpenAITranslator(api_key=settings.openai_api_key, model=settings.openai_model)