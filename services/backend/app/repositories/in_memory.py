from app.repositories.base import MessageRepository, StoredMessage


class InMemoryMessageRepository(MessageRepository):
    def __init__(self) -> None:
        self.storage: dict[str, list[StoredMessage]] = {}

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
    ) -> None:
        messages = self._get_list_message_by_room(room=room)
        messages.append(
            StoredMessage(
                message_id=message_id,
                room=room,
                sender_nickname=sender_nickname,
                sender_language=sender_language,
                original_text=original_text,
                translations=translations,
                sent_at=sent_at,
            )
        )

    async def get_messages(self, *, room: str) -> list[StoredMessage]:
        messages = self._get_list_message_by_room(room=room)
        return [message for message in messages if message.room == room]

    async def get_recent_messages(
        self, *, room: str, number_of_messages: int
    ) -> list[StoredMessage]:
        if number_of_messages <= 0:
            return []
        messages = self._get_list_message_by_room(room=room)
        messages_size: int = len(messages)
        if number_of_messages >= messages_size:
            return messages
        result: list[StoredMessage] = list()
        start_index = -number_of_messages

        for index in range(start_index, messages_size):
            message = messages[index]
            result.append(message)
            if len(result) == number_of_messages:
                return result

        return result

    def _get_list_message_by_room(self, *, room: str) -> list[StoredMessage]:
        list_messages: list[StoredMessage] | None = self.storage.get(room)
        if list_messages is None:
            list_messages = list()
            self.storage.setdefault(room, list_messages)

        return list_messages
