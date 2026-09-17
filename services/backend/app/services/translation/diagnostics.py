import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from time import perf_counter_ns
from uuid import uuid4

logger = logging.getLogger("uvicorn.error.translation_performance")


def elapsed_ms(start_ns: int, end_ns: int | None = None) -> float:
    completed_ns = perf_counter_ns() if end_ns is None else end_ns
    return round((completed_ns - start_ns) / 1_000_000, 3)


@dataclass
class TranslationDiagnostics:
    room_id: str
    message_id: str
    source_language: str
    target_language_count: int
    room_connection_count: int
    message_received_ns: int
    operation_type: str = "room_message"
    validation_ms: float = 0.0
    translation_operation_id: str = field(default_factory=lambda: str(uuid4()))
    status: str = "in_progress"
    recent_context_message_count: int = 0
    context_summary_character_count: int = 0
    recent_context_character_count: int = 0
    application_prompt_character_count: int | None = None
    original_broadcast_ms: float | None = None
    prompt_build_ms: float | None = None
    openai_total_ms: float | None = None
    openai_processing_ms: float | None = None
    domain_response_processing_ms: float | None = None
    translation_broadcast_ms: float | None = None
    repository_save_ms: float | None = None
    translation_pipeline_ms: float | None = None
    message_to_translation_update_ms: float | None = None
    handler_total_ms: float | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None
    reasoning_tokens: int | None = None
    cached_input_tokens: int | None = None
    retry_count: int | None = None
    model: str | None = None
    service_tier: str | None = None
    openai_response_id: str | None = None
    openai_request_id: str | None = None
    http_status_code: int | None = None
    failure_stage: str | None = None
    error_type: str | None = None

    def mark_failed(self, *, stage: str, error: BaseException) -> None:
        self.status = "failed"
        self.failure_stage = stage
        cause = error.__cause__ or error
        self.error_type = type(cause).__name__

    def to_event(self) -> dict[str, object]:
        event = asdict(self)
        event.pop("message_received_ns")
        event["event"] = "translation_performance"
        event["timestamp"] = (
            datetime.now(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")
        )
        return event


def emit_translation_performance(diagnostics: TranslationDiagnostics) -> None:
    logger.info(json.dumps(diagnostics.to_event(), separators=(",", ":"), sort_keys=True))
