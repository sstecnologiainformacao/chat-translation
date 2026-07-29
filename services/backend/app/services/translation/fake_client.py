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

        return response
