import pytest

from app.core.config import get_settings
from app.services.translation.base import (
    Message,
    TranslationContext,
    TranslationError,
    TranslationProvider,
    TranslationResult,
)
from app.services.translation.factory import create_translation_provider
from app.services.translation.fake_client import FakeClient
from app.services.translation.fake_translator import FakeTranslator
from app.services.translation.open_ai_client import OpenAIClient
from app.services.translation.open_ai_models import OpenAITranslationResponse
from app.services.translation.open_ai_translator import OpenAITranslator


async def test_translation_returns_fake_translator() -> None:
    translator: TranslationProvider = create_translation_provider()
    assert isinstance(translator, FakeTranslator)


async def test_translation_fake_translator() -> None:
    translator: TranslationProvider = FakeTranslator()
    context: TranslationContext = TranslationContext(context="", messages=[])

    result: TranslationResult = await translator.translate(
        text="hello",
        source_language="Portuguese",
        target_languages=set(["English"]),
        context=context,
    )

    assert result.translations == {"English": "Portuguese -> English + hello"}


async def test_open_ai_translation_check_values() -> None:
    open_ai_translation = OpenAITranslator(api_key="the-key", model="the-model")

    assert open_ai_translation.get_api_key() == "the-key"
    assert open_ai_translation.get_model() == "the-model"


async def test_return_fake_translator_if_development() -> None:
    translator: TranslationProvider = create_translation_provider()

    assert isinstance(translator, FakeTranslator)


async def test_return_open_ai_translator_if_not_development(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-fake-test")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-5.4-fake")
    monkeypatch.setenv("IS_DEVELOPMENT", "False")
    get_settings.cache_clear()

    translator: TranslationProvider = create_translation_provider()

    assert isinstance(translator, OpenAITranslator)
    assert translator._api_key == "sk-fake-test"
    assert translator._model == "gpt-5.4-fake"
    assert translator._client is not None
    assert isinstance(translator._client, OpenAIClient)
    assert translator._client._api_key == "sk-fake-test"


async def test_build_parameters_to_send_open_ai() -> None:
    translator: OpenAITranslator = OpenAITranslator(api_key="the-key", model="the-model")

    result: dict[str, object] = translator._build_api_parameters(
        text="Test",
        source_language="Portuguese",
        target_languages=set(["English", "Spanish"]),
        context=TranslationContext(
            context="The context", messages=[Message(message="a message", nickname="JL")]
        ),
    )

    expected_result = {
        "model": "the-model",
        "reasoning": {"effort": "low"},
        "instructions": (
            "You're a great translator. "
            'You need to translate the text present on the attribute "input" '
            "and that was wrote in Portuguese to English, Spanish. "
            'Translate the text using this context "The context", '
            "and the last messages: nickname: JL, message: a message;"
        ),
        "input": "Test",
    }

    assert result["model"] == expected_result["model"]
    assert result["instructions"] == expected_result["instructions"]
    assert result["input"] == expected_result["input"]


async def test_parse_open_ai_response() -> None:
    translator: OpenAITranslator = OpenAITranslator(api_key="the-key", model="the-model")

    response: dict[str, object] = {
        "translations": {
            "English": "This is a message",
            "Portuguese": "Essa é uma mensagem",
        },
        "context_update": {
            "summary": "It's a summary",
            "tone": "This the tone",
            "entities": [],
            "glossary": {},
        },
    }

    result: TranslationResult = translator._parse_open_ai_response(response=response)

    translations = {
        "English": "This is a message",
        "Portuguese": "Essa é uma mensagem",
    }
    context_update = {
        "summary": "It's a summary",
        "tone": "This the tone",
        "entities": [],
        "glossary": {},
    }

    assert result.translations is not None
    assert result.translations == translations
    assert result.context_update is not None
    assert result.context_update.entities == context_update["entities"]
    assert result.context_update.glossary == context_update["glossary"]
    assert result.context_update.summary == context_update["summary"]


async def test_call_fake_api() -> None:
    fake_client = FakeClient()

    translator: OpenAITranslator = OpenAITranslator(
        api_key="the-key",
        model="the-model",
        client=fake_client,
    )

    result: TranslationResult = await translator.translate(
        text="a text",
        source_language="Portuguese",
        target_languages=set(["English", "Spanish"]),
        context=TranslationContext(
            context="The context", messages=[Message(message="a message", nickname="JL")]
        ),
    )

    translations = {
        "English": "This is a message",
        "Portuguese": "Essa é uma mensagem",
    }
    context_update = {
        "summary": "It's a summary",
        "tone": "This the tone",
        "entities": [],
        "glossary": {},
    }

    assert result.translations is not None
    assert result.translations == translations
    assert result.translations.get("English") == "This is a message"
    assert result.translations.get("Portuguese") == "Essa é uma mensagem"
    assert result.context_update is not None
    assert result.context_update.entities == context_update["entities"]
    assert len(result.context_update.entities) == 0
    assert result.context_update.glossary == context_update["glossary"]
    assert result.context_update.summary == context_update["summary"]

    assert fake_client.received_api_parameters.get("model") == "the-model"
    assert fake_client.received_api_parameters.get("input") == "a text"


@pytest.mark.parametrize(
    "response",
    [
        {
            "translations": {
                "English": 123,
            },
            "context_update": {
                "summary": "It's a summary",
                "tone": "This is tone",
                "entities": [],
                "glossary": {},
            },
        },
        {
            "translations": {
                "English": "123",
                123: "Invalid key",
            },
            "context_update": {
                "summary": "It's a summary",
                "tone": "This is tone",
                "entities": [],
                "glossary": {},
            },
        },
        {
            "translations": {
                "English": "123",
            },
            "context_update": {
                "summary": "It's a summary",
                "tone": "This is tone",
                "entities": [123],
                "glossary": {},
            },
        },
        {
            "translations": {
                "English": "123",
            },
            "context_update": {
                "summary": "It's a summary",
                "tone": "This is tone",
                "entities": [],
                "glossary": {
                    "hello": 123,
                },
            },
        },
        {
            "translations": {
                "English": "123",
            },
            "context_update": None,
        },
    ],
)
async def test_parse_open_ai_response_raises_error_for_invalid_response(
    response: dict[str, object],
) -> None:
    translator = OpenAITranslator(api_key="the-key", model="the-model")

    with pytest.raises(TranslationError):
        translator._parse_open_ai_response(response=response)


async def test_open_ai_client_initializes_sdk_with_api_key() -> None:
    open_ai_client = OpenAIClient(api_key="the-key")

    assert open_ai_client._async_open_ai is not None


class FakeOutputParsed:
    def __init__(self, *, fake_response: dict[str, object] | None = None) -> None:
        self.parameters: dict[str, object] = {}
        self._fake_response = fake_response

    def model_dump(self) -> dict[str, object]:
        if self._fake_response is None:
            return {}
        return self._fake_response


class FakeParsedResponse:
    def __init__(self, *, fake_response: dict[str, object] | None = None) -> None:
        self.output_parsed = FakeOutputParsed(fake_response=fake_response)


class Responses:
    def __init__(self, *, fake_response: dict[str, object] | None = None) -> None:
        self.parameters: dict[str, object] = {}
        self._fake_response = fake_response

    async def parse(self, **parameters: object) -> FakeParsedResponse:
        self.parameters = parameters
        if self._fake_response is None:
            return FakeParsedResponse()
        return FakeParsedResponse(fake_response=self._fake_response)


class FakeAsyncOpenAI:
    def __init__(self, *, fake_response: dict[str, object] | None = None) -> None:
        self.responses = Responses(fake_response=fake_response)


class ResponsesError:
    async def parse(self, **parameters: object) -> FakeParsedResponse:
        raise Exception("Something wrong happened")


class FakeAsyncOpenAIWithResponseError:
    def __init__(self) -> None:
        self.responses = ResponsesError()


async def test_open_ai_client_accepts_injected_sdk() -> None:
    open_ai_client = OpenAIClient(async_open_ai=FakeAsyncOpenAI())

    assert open_ai_client._async_open_ai is not None


async def test_open_ai_client_sends_parameters_to_sdk() -> None:
    fake = FakeAsyncOpenAI()

    parameters: dict[str, object] = {
        "param1": "The param 1",
        "param2": "The param 2",
    }

    open_ai_client = OpenAIClient(async_open_ai=fake)
    await open_ai_client.translate(api_parameters=parameters)

    assert fake.responses.parameters is not None
    assert fake.responses.parameters.get("param1") == "The param 1"
    assert fake.responses.parameters.get("param2") == "The param 2"
    assert fake.responses.parameters.get("text_format") is OpenAITranslationResponse


async def test_open_ai_client_returns_parsed_response_dump() -> None:
    expected_result = {
        "translations": {
            "English": "This is a message",
            "Portuguese": "Essa é uma mensagem",
        },
        "context_update": {
            "summary": "It's a summary",
            "tone": "This the tone",
            "entities": [],
            "glossary": {},
        },
    }
    fake = FakeAsyncOpenAI(fake_response=expected_result)

    parameters: dict[str, object] = {
        "param1": "The param 1",
        "param2": "The param 2",
    }

    open_ai_client = OpenAIClient(async_open_ai=fake)
    result = await open_ai_client.translate(api_parameters=parameters)

    assert result == expected_result


async def test_open_ai_client_raises_translation_error_when_sdk_fails() -> None:
    fake = FakeAsyncOpenAIWithResponseError()

    parameters: dict[str, object] = {
        "param1": "The param 1",
        "param2": "The param 2",
    }

    open_ai_client = OpenAIClient(async_open_ai=fake)

    with pytest.raises(TranslationError):
        await open_ai_client.translate(api_parameters=parameters)
