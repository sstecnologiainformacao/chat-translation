from openai import OpenAI


class OpenAITranslator:
    def __init__(self, *, api_key: str, model: str):
        self._api_key = api_key
        self._model = model
        self._client = OpenAI(
            api_key=api_key,
            base_url="https://api.openai.com/v1",
            model=model,
            timeout=20.0,
            max_retries=3,
        )
        
    async def translate(self, *, text: str, source_language: str, target_language: list[str] -> str:
        response = self._client.responses.create(
            model="gpt-5.5",
            instructions="You are a coding assistant that talks like a pirate.",
            input="How do I check if a Python object is an instance of a class?",
        )