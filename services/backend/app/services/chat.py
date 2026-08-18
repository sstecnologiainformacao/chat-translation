from typing import Protocol

from app.repositories.base import MessageRepository, StoredMessage
from app.services.translation.base import (
    Message,
    TranslationContext,
    TranslationError,
    TranslationProvider,
    TranslationResult,
)


class WebSocketLike(Protocol):
    async def send_json(self, data: dict[str, object]) -> None:
        pass


class ActiveConnection:
    def __init__(self, ws: WebSocketLike, *, nickname: str, language: str) -> None:
        self.ws = ws
        self.nickname = nickname
        self.language = language


class Conversation:
    def __init__(self, *, key: str):
        self.context: TranslationContext = TranslationContext.new_instance()
        self.connections: set[ActiveConnection] = set[ActiveConnection]()
        self.key: str = key
        self.messages: list[Message] = list[Message]()

    def get_key(self) -> str:
        return self.key

    def add_coonection(self, connection: ActiveConnection) -> None:
        self.connections.add(connection)

    def remove_connection(self, connection: ActiveConnection) -> None:
        self.connections.discard(connection)

    def add_message(self, *, message: Message) -> None:
        self.messages.append(message)

        if len(self.context.messages) == 5:
            self.context.messages.pop(0)

        self.context.messages.append(message)

    def update_context(self, *, new_context: str) -> None:
        self.context.context = new_context


class ConnectionManager:
    def __init__(self, *, max_connections: int = 2) -> None:
        self.max_connections = max_connections
        self._connections: list[ActiveConnection] = []
        self._rooms: dict[str, Conversation] = {}

    async def connect(
        self,
        ws: WebSocketLike,
        *,
        nickname: str,
        language: str,
    ) -> ActiveConnection:
        connection = ActiveConnection(ws, nickname=nickname, language=language)
        self._connections.append(connection)
        return connection

    async def disconnect(self, connection: ActiveConnection) -> None:
        if connection in self._connections:
            self._connections.remove(connection)

        for conversation in self._rooms.values():
            if connection in conversation.connections:
                conversation.connections.remove(connection)

    async def join_room(self, connection: ActiveConnection, *, room: str) -> None:
        conversation: Conversation = self.get_room(room=room)
        if conversation is not None:
            conversation.add_coonection(connection)

    async def leave_room(self, connection: ActiveConnection, *, room: str) -> None:
        conversation: Conversation | None = self._rooms.get(room)
        if conversation is not None:
            conversation.remove_connection(connection)

    async def broadcast_to_room(self, room: str, message: dict[str, object]) -> None:
        conversation: Conversation = self._rooms.get(room, Conversation(key=room))

        for connection in conversation.connections:
            await self.send_to(connection, message)

    def room_connection_count(self, room: str) -> int:
        conversation: Conversation = self._rooms.get(room, Conversation(key=room))
        return len(conversation.connections)

    async def send_to(
        self,
        connection: ActiveConnection,
        message: dict[str, object],
    ) -> None:
        await connection.ws.send_json(message)

    async def broadcast(self, message: dict[str, object]) -> None:
        for connection in self._connections:
            await self.send_to(connection, message)

    def connection_count(self) -> int:
        return len(self._connections)

    def find_by_nickname(self, nickname: str) -> ActiveConnection | None:
        for connection in self._connections:
            if connection.nickname == nickname:
                return connection

        return None

    def target_languages_room(self, *, language: str, room: str) -> set[str]:
        conversation: Conversation | None = self.get_room(room=room)
        if conversation is not None:
            languages: set[str] = set()

            if conversation is None:
                return languages

            for connection in conversation.connections:
                if connection.language != language:
                    languages.add(connection.language)

            return languages

        return set()

    def get_room(self, *, room: str) -> Conversation:
        conversation: Conversation | None = self._rooms.get(room)

        if conversation is None:
            conversation = Conversation(key=room)
            self._rooms[room] = conversation

        return conversation


class ChatService:
    def __init__(
        self,
        manager: ConnectionManager,
        translator: TranslationProvider,
        repository: MessageRepository,
    ) -> None:
        self.translator: TranslationProvider = translator
        self._manager = manager
        self.repository: MessageRepository = repository

    def build_room_key(self, raw_key: str) -> str:
        room_name = raw_key
        if raw_key == "general":
            room_name = f"room:{raw_key}"
        return room_name

    async def join_public_room(
        self,
        connection: ActiveConnection,
        *,
        room: str,
    ) -> None:
        await self._manager.join_room(connection, room=room)

        message: dict[str, object] = {
            "type": "system_event",
            "event": "user_joined",
            "room": room,
            "nickname": connection.nickname,
            "language": connection.language,
        }

        await self._manager.broadcast_to_room(room, message)

    async def leave_public_room(
        self,
        connection: ActiveConnection,
        *,
        room: str,
    ) -> None:
        await self._manager.leave_room(connection, room=room)

        message: dict[str, object] = {
            "type": "system_event",
            "event": "user_left",
            "room": room,
            "nickname": connection.nickname,
            "language": connection.language,
        }

        await self._manager.broadcast_to_room(room, message)

    async def send_private_message(
        self,
        sender: ActiveConnection,
        *,
        recipient_nickname: str,
        text: str,
        message_id: str,
        sent_at: str,
    ) -> None:
        recipient = self._manager.find_by_nickname(recipient_nickname)

        if recipient is None:
            error_message: dict[str, object] = {
                "type": "error",
                "reason": "recipient_not_found",
            }

            await self._manager.send_to(sender, error_message)
            return

        try:
            sorted_users_nicks = sorted([sender.nickname, recipient_nickname])
            room = f"private:{':'.join(sorted_users_nicks)}"
            conversation: Conversation | None = self._get_room(room=room)

            if conversation is not None:
                translations = await self._translate_text(
                    sender=sender,
                    list_languages=set([recipient.language]),
                    text=text,
                    context=conversation.context,
                )

                result_translation = {}
                if translations is not None:
                    result_translation = translations.translations

                message: dict[str, object] = {
                    "type": "private_message",
                    "message_id": message_id,
                    "sender_nickname": sender.nickname,
                    "sender_language": sender.language,
                    "recipient_nickname": recipient.nickname,
                    "original_text": text,
                    "translations": result_translation,
                    "sent_at": sent_at,
                }

                if translations is not None and translations.context_update is not None:
                    conversation.update_context(new_context=translations.context_update.summary)
                await self._manager.send_to(sender, message)
                await self._manager.send_to(recipient, message)
                await self.repository.save_message(
                    message_id=message_id,
                    room=room,
                    sender_nickname=sender.nickname,
                    sender_language=sender.language,
                    original_text=text,
                    translations=result_translation,
                    sent_at=sent_at,
                )
            else:
                raise TranslationError
        except TranslationError:
            await self._manager.send_to(
                sender,
                {
                    "type": "error",
                    "reason": "translation_failed",
                },
            )
            return

    async def send_room_message(
        self,
        sender: ActiveConnection,
        *,
        text: str,
        message_id: str,
        sent_at: str,
    ) -> None:

        list_languages: set[str] = self._check_languages_to_translate(
            sender=sender, room=self._get_key_room_general()
        )

        conversation: Conversation | None = self._get_room(room=self._get_key_room_general())

        try:
            if conversation is not None:
                translations_result: TranslationResult | None = await self._translate_text(
                    sender=sender,
                    list_languages=list_languages,
                    text=text,
                    context=conversation.context,
                )

                if (
                    translations_result is not None
                    and translations_result.context_update is not None
                ):
                    conversation.update_context(
                        new_context=translations_result.context_update.summary
                    )

                translations_dict = getattr(translations_result, "translations", {})

                message: dict[str, object] = {
                    "type": "room_message",
                    "message_id": message_id,
                    "room": "general",
                    "sender_nickname": sender.nickname,
                    "sender_language": sender.language,
                    "original_text": text,
                    "translations": translations_dict,
                    "sent_at": sent_at,
                }

                original_message = Message(message=text, nickname=sender.nickname)
                conversation.add_message(message=original_message)
                await self._manager.broadcast_to_room(self._get_key_room_general(), message)
                await self.repository.save_message(
                    message_id=message_id,
                    room="general",
                    sender_nickname=sender.nickname,
                    sender_language=sender.language,
                    original_text=text,
                    translations=translations_dict,
                    sent_at=sent_at,
                )
        except TranslationError:
            await self._manager.send_to(
                sender,
                {
                    "type": "error",
                    "reason": "translation_failed",
                },
            )
            return

    def _check_languages_to_translate(self, *, sender: ActiveConnection, room: str) -> set[str]:
        return self._manager.target_languages_room(
            language=sender.language,
            room=room,
        )

    def _get_room(self, *, room: str) -> Conversation:
        return self._manager.get_room(room=room)

    def _get_key_room_general(self) -> str:
        return "room:general"

    async def _translate_text(
        self,
        *,
        sender: ActiveConnection,
        list_languages: set[str],
        text: str,
        context: TranslationContext,
    ) -> TranslationResult | None:
        if len(list_languages) == 0:
            return None

        new_list_languages = set(list_languages)
        new_list_languages.discard(sender.language)

        return await self.translator.translate(
            text=text,
            source_language=sender.language,
            target_languages=new_list_languages,
            context=TranslationContext(context=context.context, messages=context.messages),
        )

    async def connect(
        self,
        ws: WebSocketLike,
        *,
        nickname: str,
        language: str,
    ) -> ActiveConnection:
        return await self._manager.connect(ws, nickname=nickname, language=language)

    async def join_room(self, connection: ActiveConnection, *, room: str) -> None:
        room_key = self.build_room_key(room)
        await self._manager.join_room(connection, room=room_key)
        messages: list[StoredMessage] = await self.repository.get_recent_messages(
            room=room, number_of_messages=5
        )

        if len(messages) >= 1:
            messages_history: list[dict[str, object]] = []
            for message in messages:
                translations = message.translations
                if (
                    connection.language != message.sender_language
                    and connection.language not in translations
                ):
                    conversation: Conversation | None = self._get_room(room=room_key)
                    languages: set[str] = set()
                    languages.add(connection.language)
                    if conversation is not None:
                        result: TranslationResult | None = await self.translator.translate(
                            text=message.original_text,
                            source_language=message.sender_language,
                            target_languages=languages,
                            context=conversation.context,
                        )
                        if result is not None:
                            translations = {**translations, **result.translations}

                message_history: dict[str, object] = {
                    "type": "room_history",
                    "message_id": message.message_id,
                    "sender_nickname": message.sender_nickname,
                    "sender_language": message.sender_language,
                    "original_text": message.original_text,
                    "translations": translations,
                    "sent_at": message.sent_at,
                }
                messages_history.append(message_history)

            payload_history: dict[str, object] = {
                "type": "room_history",
                "room": room,
                "messages": messages_history,
            }
            await self._manager.send_to(connection, payload_history)

    async def disconnect(self, connection: ActiveConnection) -> None:
        await self._manager.disconnect(connection=connection)
