from pydantic import BaseModel, ConfigDict


class OpenAIContextUpdateResponse(BaseModel):
    model_config = ConfigDict(strict=True)

    summary: str
    tone: str
    entities: list[str]
    glossary: dict[str, str]


class OpenAITranslationResponse(BaseModel):
    model_config = ConfigDict(strict=True)

    translations: dict[str, str]
    context_update: OpenAIContextUpdateResponse
