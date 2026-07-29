from pydantic import BaseModel, ConfigDict


class OpenAIGlossaryItem(BaseModel):
    term: str
    translation: str


class OpenAIContextUpdateResponse(BaseModel):
    model_config = ConfigDict(strict=True)

    summary: str
    tone: str
    entities: list[str]
    glossary: list[OpenAIGlossaryItem]


class OpenAITranslationItem(BaseModel):
    language: str
    text: str


class OpenAITranslationResponse(BaseModel):
    model_config = ConfigDict(strict=True)

    translations: list[OpenAITranslationItem]
    context_update: OpenAIContextUpdateResponse
