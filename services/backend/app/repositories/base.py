from typing import Protocol


class StoredMessage:
    def __init__(
        self,
        *,
        message_id: str,
        room: str,
        sender_nickname: str,
        sender_language: str,
        original_text: str,
        translations: dict[str, str],
        sent_at: str,
    ) -> None:
        self.message_id = message_id
        self.room = room
        self.sender_nickname = sender_nickname
        self.sender_language = sender_language
        self.original_text = original_text
        self.translations = translations
        self.sent_at = sent_at


class MessageRepository(Protocol):
    async def save_message(
        self,
        *,
        message_id: str,
        room: str,
        sender_nickname: str,
        sender_language: str,
        original_text: str,
        translations: dict[str, str],
        sent_at: str,
    ) -> None: ...

    async def get_messages(self, *, room: str) -> list[StoredMessage]: ...

    async def get_recent_messages(
        self, *, room: str, number_of_messages: int
    ) -> list[StoredMessage]: ...
