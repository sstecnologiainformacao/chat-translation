from app.services.translation.base import TranslationClient


class FakeClient(TranslationClient):
    def __init__(self) -> None:
        self._received_api_parameters: dict[str, object] = {}

    @property
    def received_api_parameters(self) -> dict[str, object]:
        return self._received_api_parameters

    async def translate(self, *, api_parameters: dict[str, object]) -> dict[str, object]:
        self._received_api_parameters = api_parameters

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

        return response
