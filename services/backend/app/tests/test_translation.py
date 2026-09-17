import pytest

from app.core.config import get_settings
from app.services.translation.base import (
    Message,
    TranslationContext,
    TranslationError,
    TranslationProvider,
    TranslationResult,
)
from app.services.translation.diagnostics import TranslationDiagnostics
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
            "Return translations for each target language and update the translation context"
            " as context_update with summary, tone, entities, and glossary. "
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


async def test_build_api_parameters_has_correct_params() -> None:
    translator: OpenAITranslator = OpenAITranslator(api_key="the-key", model="the-model")

    result: dict[str, object] = translator._build_api_parameters(
        text="Test",
        source_language="Portuguese",
        target_languages=set(["English", "Spanish"]),
        context=TranslationContext(
            context="The context", messages=[Message(message="a message", nickname="JL")]
        ),
    )

    result_instructions = result.get("instructions")

    assert isinstance(result_instructions, str)
    assert "translations" in result_instructions
    assert "context_update" in result_instructions
    assert "summary" in result_instructions
    assert "tone" in result_instructions
    assert "entities" in result_instructions
    assert "glossary" in result_instructions


async def test_parse_open_ai_response() -> None:
    translator: OpenAITranslator = OpenAITranslator(api_key="the-key", model="the-model")

    response: dict[str, object] = {
        "translations": [
            {"language": "English", "text": "This is a message"},
            {"language": "Portuguese", "text": "Essa é uma mensagem"},
        ],
        "context_update": {
            "summary": "It's a summary",
            "tone": "This the tone",
            "entities": [],
            "glossary": [],
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


async def test_open_ai_translator_records_prompt_and_domain_processing_metrics() -> None:
    fake_client = FakeClient()
    translator = OpenAITranslator(api_key="the-key", model="the-model", client=fake_client)
    diagnostics = TranslationDiagnostics(
        room_id="general",
        message_id="msg-1",
        source_language="Portuguese",
        target_language_count=1,
        room_connection_count=2,
        message_received_ns=1,
    )

    await translator.translate(
        text="a text",
        source_language="Portuguese",
        target_languages={"English"},
        context=TranslationContext(
            context="The context",
            messages=[Message(message="a message", nickname="JL")],
        ),
        diagnostics=diagnostics,
    )

    instructions = fake_client.received_api_parameters["instructions"]
    assert diagnostics.prompt_build_ms is not None
    assert diagnostics.domain_response_processing_ms is not None
    assert diagnostics.application_prompt_character_count == len(str(instructions)) + len("a text")


@pytest.mark.parametrize(
    "response",
    [
        {
            "translations": [
                {"language": "English", "text": 123},
            ],
            "context_update": {
                "summary": "It's a summary",
                "tone": "This is tone",
                "entities": [],
                "glossary": [],
            },
        },
        {
            "translations": [
                {"language": "English", "text": "123"},
                {"language": 123, "text": "Invalid key"},
            ],
            "context_update": {
                "summary": "It's a summary",
                "tone": "This is tone",
                "entities": [],
                "glossary": [],
            },
        },
        {
            "translations": [
                {"language": "English", "text": "123"},
            ],
            "context_update": {
                "summary": "It's a summary",
                "tone": "This is tone",
                "entities": [123],
                "glossary": [],
            },
        },
        {
            "translations": [
                {"language": "English", "text": "123"},
            ],
            "context_update": {
                "summary": "It's a summary",
                "tone": "This is tone",
                "entities": [],
                "glossary": [
                    {"term": "hello", "translation": 123},
                ],
            },
        },
        {
            "translations": [
                {"language": "English", "text": "123"},
            ],
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


class FakeInputTokenDetails:
    def __init__(self, *, cached_tokens: int) -> None:
        self.cached_tokens = cached_tokens


class FakeOutputTokenDetails:
    def __init__(self, *, reasoning_tokens: int) -> None:
        self.reasoning_tokens = reasoning_tokens


class FakeResponseUsage:
    def __init__(
        self,
        *,
        input_tokens: int,
        output_tokens: int,
        total_tokens: int,
        cached_tokens: int,
        reasoning_tokens: int,
    ) -> None:
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
        self.total_tokens = total_tokens
        self.input_tokens_details = FakeInputTokenDetails(cached_tokens=cached_tokens)
        self.output_tokens_details = FakeOutputTokenDetails(reasoning_tokens=reasoning_tokens)


class FakeParsedResponse:
    def __init__(
        self,
        *,
        fake_response: dict[str, object] | None = None,
        response_id: str = "resp-test",
        request_id: str | None = "req-test",
        model: str = "gpt-5.4-mini",
        service_tier: str | None = "default",
        usage: FakeResponseUsage | None = None,
    ) -> None:
        self.output_parsed = FakeOutputParsed(fake_response=fake_response)
        self.id = response_id
        self._request_id = request_id
        self.model = model
        self.service_tier = service_tier
        self.usage = usage


class FakeRawResponse:
    def __init__(
        self,
        *,
        fake_response: dict[str, object] | None = None,
        parsed_response: FakeParsedResponse | None = None,
        request_id: str | None = "req-test",
        retries_taken: int = 0,
        status_code: int = 200,
        headers: dict[str, str] | None = None,
    ) -> None:
        self.request_id = request_id
        self.retries_taken = retries_taken
        self.status_code = status_code
        self.headers = headers or {}
        self._parsed_response = parsed_response or FakeParsedResponse(fake_response=fake_response)

    def parse(self) -> FakeParsedResponse:
        return self._parsed_response


class RawResponses:
    def __init__(self, *, raw_response: FakeRawResponse) -> None:
        self.parameters: dict[str, object] = {}
        self._raw_response = raw_response

    async def parse(self, **parameters: object) -> FakeRawResponse:
        self.parameters = parameters
        return self._raw_response


class Responses:
    def __init__(
        self,
        *,
        fake_response: dict[str, object] | None = None,
        raw_response: FakeRawResponse | None = None,
    ) -> None:
        self.with_raw_response = RawResponses(
            raw_response=raw_response or FakeRawResponse(fake_response=fake_response)
        )

    @property
    def parameters(self) -> dict[str, object]:
        return self.with_raw_response.parameters


class FakeAsyncOpenAI:
    def __init__(
        self,
        *,
        fake_response: dict[str, object] | None = None,
        raw_response: FakeRawResponse | None = None,
    ) -> None:
        self.responses = Responses(fake_response=fake_response, raw_response=raw_response)


class RawResponsesError:
    async def parse(self, **parameters: object) -> FakeRawResponse:
        raise Exception("Something wrong happened")


class ResponsesError:
    def __init__(self) -> None:
        self.with_raw_response = RawResponsesError()


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
    expected_result: dict[str, object] = {
        "translations": [
            {"language": "English", "text": "This is a message"},
            {"language": "Portuguese", "text": "Essa é uma mensagem"},
        ],
        "context_update": {
            "summary": "It's a summary",
            "tone": "This the tone",
            "entities": [],
            "glossary": [],
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


def make_diagnostics(*, message_id: str = "msg-1") -> TranslationDiagnostics:
    return TranslationDiagnostics(
        room_id="general",
        message_id=message_id,
        source_language="Portuguese",
        target_language_count=2,
        room_connection_count=3,
        message_received_ns=1,
    )


async def test_open_ai_client_propagates_usage_and_response_metadata() -> None:
    usage = FakeResponseUsage(
        input_tokens=612,
        output_tokens=94,
        total_tokens=706,
        cached_tokens=128,
        reasoning_tokens=18,
    )
    parsed_response = FakeParsedResponse(
        usage=usage,
        response_id="resp-123",
        request_id="req-123",
        model="gpt-5.4-mini",
        service_tier="default",
    )
    raw_response = FakeRawResponse(
        parsed_response=parsed_response,
        request_id="req-123",
        retries_taken=1,
        status_code=200,
        headers={"openai-processing-ms": "241.5"},
    )
    fake = FakeAsyncOpenAI(raw_response=raw_response)
    diagnostics = make_diagnostics()

    await OpenAIClient(async_open_ai=fake).translate(
        api_parameters={"model": "gpt-5.4-mini"},
        diagnostics=diagnostics,
    )

    assert diagnostics.input_tokens == 612
    assert diagnostics.output_tokens == 94
    assert diagnostics.total_tokens == 706
    assert diagnostics.cached_input_tokens == 128
    assert diagnostics.reasoning_tokens == 18
    assert diagnostics.retry_count == 1
    assert diagnostics.openai_processing_ms == 241.5
    assert diagnostics.http_status_code == 200
    assert diagnostics.model == "gpt-5.4-mini"
    assert diagnostics.service_tier == "default"
    assert diagnostics.openai_response_id == "resp-123"
    assert diagnostics.openai_request_id == "req-123"
    assert diagnostics.openai_total_ms is not None
    assert fake.responses.parameters["extra_headers"] == {
        "X-Client-Request-Id": diagnostics.translation_operation_id
    }


async def test_open_ai_client_allows_missing_optional_metadata() -> None:
    parsed_response = FakeParsedResponse(
        request_id=None,
        service_tier=None,
        usage=None,
    )
    raw_response = FakeRawResponse(
        parsed_response=parsed_response,
        request_id=None,
        headers={},
    )
    diagnostics = make_diagnostics()

    await OpenAIClient(async_open_ai=FakeAsyncOpenAI(raw_response=raw_response)).translate(
        api_parameters={"model": "gpt-5.4-mini"},
        diagnostics=diagnostics,
    )

    assert diagnostics.input_tokens is None
    assert diagnostics.cached_input_tokens is None
    assert diagnostics.openai_processing_ms is None
    assert diagnostics.openai_request_id is None
    assert diagnostics.service_tier is None


async def test_open_ai_client_records_failure_diagnostics() -> None:
    diagnostics = make_diagnostics()

    with pytest.raises(TranslationError):
        await OpenAIClient(async_open_ai=FakeAsyncOpenAIWithResponseError()).translate(
            api_parameters={"model": "gpt-5.4-mini"},
            diagnostics=diagnostics,
        )

    assert diagnostics.status == "failed"
    assert diagnostics.failure_stage == "openai_request"
    assert diagnostics.error_type == "Exception"
    assert diagnostics.openai_total_ms is not None
