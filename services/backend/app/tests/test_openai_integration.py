import os

import pytest

from app.services.translation.base import TranslationContext
from app.services.translation.open_ai_client import OpenAIClient
from app.services.translation.open_ai_translator import OpenAITranslator

pytestmark = pytest.mark.integration


def should_run_openai_integration_test() -> bool:
    return (
        os.environ.get("RUN_OPENAI_INTEGRATION_TESTS") == "true"
        and os.environ.get("OPENAI_INTEGRATION_API_KEY") is not None
    )


@pytest.mark.skipif(
    not should_run_openai_integration_test(),
    reason=(
        "Set RUN_OPENAI_INTEGRATION_TESTS=true and OPENAI_INTEGRATION_API_KEY "
        "to run the real OpenAI integration test."
    ),
)
async def test_openai_api_translates_text_with_real_client() -> None:
    api_key = os.environ["OPENAI_INTEGRATION_API_KEY"]
    model = os.environ.get("OPENAI_INTEGRATION_MODEL", "gpt-5.4-mini")
    source_text = "Ola, como voce esta?"
    client = OpenAIClient(api_key=api_key)
    translator = OpenAITranslator(api_key=api_key, model=model, client=client)

    print("OpenAI integration test is enabled.")
    print(f"Model: {model}")
    print(f"Source text: {source_text}")
    print("Target language: English")

    result = await translator.translate(
        text=source_text,
        source_language="Portuguese",
        target_languages={"English"},
        context=TranslationContext.new_instance(),
    )
    translated_text = result.translations["English"]

    print("OpenAI API key was accepted by the API.")
    print(f"Translation result: {translated_text}")

    assert translated_text
    assert translated_text != source_text
