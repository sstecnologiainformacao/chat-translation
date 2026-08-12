from typing import Protocol


class StoredUser:
    def __init__(self, *, username: str, password_hash: str, language: str, nickname: str) -> None:
        self.username = username
        self.password_hash = password_hash
        self.language = language
        self.nickname = nickname


class UserRepository(Protocol):
    async def create_user(
        self, *, username: str, password_hash: str, nickname: str, language: str
    ) -> bool: ...

    async def get_user(self, *, username: str) -> StoredUser | None: ...


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
