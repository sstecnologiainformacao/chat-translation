from collections.abc import Mapping
from time import perf_counter_ns
from typing import Protocol, cast

from openai import APIError, APIStatusError, AsyncOpenAI

from app.services.translation.base import TranslationClient, TranslationError
from app.services.translation.diagnostics import TranslationDiagnostics, elapsed_ms
from app.services.translation.open_ai_models import OpenAITranslationResponse


class ParsedOutput(Protocol):
    def model_dump(self) -> dict[str, object]: ...


class InputTokenDetails(Protocol):
    @property
    def cached_tokens(self) -> int: ...


class OutputTokenDetails(Protocol):
    @property
    def reasoning_tokens(self) -> int: ...


class ResponseUsage(Protocol):
    @property
    def input_tokens(self) -> int: ...

    @property
    def output_tokens(self) -> int: ...

    @property
    def total_tokens(self) -> int: ...

    @property
    def input_tokens_details(self) -> InputTokenDetails: ...

    @property
    def output_tokens_details(self) -> OutputTokenDetails: ...


class ParsedResponse(Protocol):
    @property
    def output_parsed(self) -> ParsedOutput: ...

    @property
    def id(self) -> str: ...

    @property
    def model(self) -> str: ...

    @property
    def service_tier(self) -> str | None: ...

    @property
    def usage(self) -> ResponseUsage | None: ...

    @property
    def _request_id(self) -> str | None: ...


class RawResponse(Protocol):
    @property
    def request_id(self) -> str | None: ...

    @property
    def retries_taken(self) -> int: ...

    @property
    def status_code(self) -> int: ...

    @property
    def headers(self) -> Mapping[str, str]: ...

    def parse(self) -> ParsedResponse: ...


class RawResponses(Protocol):
    async def parse(self, **parameters: object) -> RawResponse: ...


class Responses(Protocol):
    @property
    def with_raw_response(self) -> RawResponses: ...


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
        diagnostics: TranslationDiagnostics | None = None,
    ) -> dict[str, object]:
        request_started_ns = perf_counter_ns()
        try:
            parameters = dict(api_parameters)
            if diagnostics is not None:
                parameters["extra_headers"] = {
                    "X-Client-Request-Id": diagnostics.translation_operation_id
                }

            raw_response = await self._async_open_ai.responses.with_raw_response.parse(
                **parameters,
                text_format=OpenAITranslationResponse,
            )
            self._capture_raw_metadata(raw_response=raw_response, diagnostics=diagnostics)

            parsed_response = raw_response.parse()
            self._capture_response_metadata(response=parsed_response, diagnostics=diagnostics)
            result = parsed_response.output_parsed.model_dump()

            if diagnostics is not None:
                diagnostics.openai_total_ms = elapsed_ms(request_started_ns)
            return result
        except Exception as error:
            if diagnostics is not None:
                diagnostics.openai_total_ms = elapsed_ms(request_started_ns)
                diagnostics.mark_failed(stage="openai_request", error=error)
                if isinstance(error, APIError):
                    retry_count = error.request.headers.get("x-stainless-retry-count")
                    if retry_count is not None:
                        try:
                            diagnostics.retry_count = int(retry_count)
                        except ValueError:
                            diagnostics.retry_count = None
                if isinstance(error, APIStatusError):
                    diagnostics.http_status_code = error.status_code
                    diagnostics.openai_request_id = error.request_id
            raise TranslationError() from error

    def _capture_raw_metadata(
        self,
        *,
        raw_response: RawResponse,
        diagnostics: TranslationDiagnostics | None,
    ) -> None:
        if diagnostics is None:
            return

        diagnostics.openai_request_id = raw_response.request_id
        diagnostics.retry_count = raw_response.retries_taken
        diagnostics.http_status_code = raw_response.status_code
        processing_ms = raw_response.headers.get("openai-processing-ms")
        if processing_ms is not None:
            try:
                diagnostics.openai_processing_ms = float(processing_ms)
            except ValueError:
                diagnostics.openai_processing_ms = None

    def _capture_response_metadata(
        self,
        *,
        response: ParsedResponse,
        diagnostics: TranslationDiagnostics | None,
    ) -> None:
        if diagnostics is None:
            return

        diagnostics.openai_response_id = response.id
        diagnostics.openai_request_id = response._request_id or diagnostics.openai_request_id
        diagnostics.model = response.model
        diagnostics.service_tier = response.service_tier

        usage = response.usage
        if usage is None:
            return

        diagnostics.input_tokens = usage.input_tokens
        diagnostics.output_tokens = usage.output_tokens
        diagnostics.total_tokens = usage.total_tokens
        diagnostics.cached_input_tokens = usage.input_tokens_details.cached_tokens
        diagnostics.reasoning_tokens = usage.output_tokens_details.reasoning_tokens
