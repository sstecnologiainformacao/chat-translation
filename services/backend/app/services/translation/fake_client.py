from app.services.translation.base import TranslationClient


class FakeClient(TranslationClient):
    async def translate(self, *, api_parameters: dict[str, object]) -> dict[str, object]:

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
