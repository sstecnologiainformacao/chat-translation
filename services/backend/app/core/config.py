from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    chat_user: str
    chat_password: str
    jwt_secret: str
    jwt_expires_minutes: int = 60
    anthropic_api_key: str
    anthropic_model: str = "claude-sonnet-4-6"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    # BaseSettings loads required fields from environment variables at runtime.
    return Settings()  # type: ignore[call-arg]
