from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    chat_user: str
    chat_password: str
    jwt_secret: str
    jwt_expires_minutes: int = 60
    openai_api_key: str
    openai_model: str = "gpt-5.4-mini"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    # BaseSettings loads required fields from environment variables at runtime.
    return Settings()  # type: ignore[call-arg]
