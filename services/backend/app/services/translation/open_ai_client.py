from typing import Protocol, cast

from openai import AsyncOpenAI

from app.services.translation.base import TranslationClient, TranslationError


class Responses(Protocol):
    async def create(self, **parameters: object) -> dict[str, object]: ...


class SimpleAsyncOpenAi(Protocol):
    @property
    def responses(self) -> Responses: ...


class OpenAIClient(TranslationClient):
    def __init__(
        self, *, api_key: str | None = None, async_open_ai: SimpleAsyncOpenAi | None = None
    ) -> None:
        if api_key is None and async_open_ai is None:
            raise TranslationError()

        if async_open_ai is not None:
            self._async_open_ai: SimpleAsyncOpenAi = async_open_ai
        else:
            self._api_key = api_key
            self._async_open_ai = cast(SimpleAsyncOpenAi, AsyncOpenAI(api_key=api_key))

    async def translate(
        self,
        *,
        api_parameters: dict[str, object],
    ) -> dict[str, object]:
        try:
            parameters = api_parameters
            return await self._async_open_ai.responses.create(**parameters)
        except Exception as error:
            raise TranslationError() from error
