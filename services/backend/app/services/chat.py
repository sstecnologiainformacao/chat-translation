from typing import Protocol

from app.services.translation.base import (
    TranslationContext,
    TranslationError,
    TranslationProvider,
    TranslationResult,
    Message,
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
        self.context: TranslationContext = TranslationContext()
        self.connections: set[ActiveConnection] = set[ActiveConnection]()
        self.key: str = f"room:{key}"
        self.messages: list[Message] = list[Message]()

    def get_key(self):
        return self.key
    
    def add_coonection(self, connection: ActiveConnection):
        self.connections.add(connection)

    def remove_connection(self, connection: ActiveConnection):
        self.connections.discard(connection)

    def add_message(self, *, message: Message):
        self.messages.append(message)

        if len(self.context.messages) == 5:
            try:
                self.context.messages.remove(0)
            except:
                ...
        
        self.context.messages.append(message)

    def update_context(self, *, new_context: str):
        self.context.context = new_context

class ConnectionManager:
    def __init__(self, *, max_connections: int = 2) -> None:
        self.max_connections = max_connections
        self._connections: list[ActiveConnection] = []
        self._rooms: dict[str, Conversation] = {}

    async def connect (
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
        
        for room_connections in self._rooms.values():
            if connection in room_connections:
                room_connections.remove(connection)

    async def join_room(self, connection: ActiveConnection, *, room: str) -> None:
        conversation: Conversation = self._rooms.setdefault(room, Conversation(key=room))
        conversation.add_coonection(connection)

    async def leave_room(self, connection: ActiveConnection, *, room: str) -> None:
        conversation: Conversation = self._rooms.get(room)
        conversation.remove_connection(connection)

    async def broadcast_to_room(
            self,
            room: str,
            message: dict[str, object]
    ) -> None:
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
        conversation: Conversation = self._rooms.get(room)
        languages: set[str] = set()

        if conversation is None:
            return languages

        for connection in conversation.connections:
            if connection.language != language:
                languages.add(connection.language)

        return languages


class ChatService:
    def __init__(self, manager: ConnectionManager, translator: TranslationProvider) -> None:
        self._manager = manager
        self.translator: TranslationProvider = translator
    
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
            "language": connection.language
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
            sent_at: str
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
            conversation: Conversation = self._get_room(f"room:{sender.nickname}:{recipient_nickname}")
            translations = await self._translate_text(
                sender=sender,
                list_languages=set([recipient.language]),
                text=text,
                context=conversation.context
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

            await self._manager.send_to(sender, message)
            await self._manager.send_to(recipient, message)
        except TranslationError:
            await self._manager.send_to(
                sender,
                {
                    "type": "error",
                    "reason": "translation_failed",
                }
            )
            return

    async def send_room_message(
        self,
        sender: ActiveConnection,
        *,
        room: str,
        text: str,
        message_id: str,
        sent_at: str,
    ) -> None:

        list_languages: set[str] = self._check_languages_to_translate(
            sender=sender,
            room=room,
        )

        conversation: Conversation = self._get_room(room)

        try: 
            translations_result: TranslationResult | None = await self._translate_text(
                sender=sender,
                list_languages=list_languages,
                text=text,
                context=conversation.context.context
            )

            translations_dict = getattr(translations_result, "translations", {})

            message: dict[str, object] = {
                "type": "room_message",
                "message_id": message_id,
                "room": room,
                "sender_nickname": sender.nickname,
                "sender_language": sender.language,
                "original_text": text,
                "translations": translations_dict,
                "sent_at": sent_at,
            }

            await self._manager.broadcast_to_room(room, message)
        except TranslationError:
            await self._manager.send_to(
                sender,
                {
                    "type": "error",
                    "reason": "translation_failed",
                }
            )
            return

    def _check_languages_to_translate(self, *, sender: ActiveConnection, room: str) -> set[str]:
        return self._manager.target_languages_room(
            language=sender.language,
            room=room,
        )
    
    def _get_room(self, *, room: str) -> Conversation:
        return self._manager._rooms.get(room);


    async def _translate_text(
        self,
        *,
        sender: ActiveConnection,
        list_languages: set[str],
        text: str,
        context: str,
    ) -> TranslationResult | None:
        if len(list_languages) == 0:
            return None

        new_list_languages = set(list_languages)
        new_list_languages.discard(sender.language)

        return await self.translator.translate(
            text=text,
            source_language=sender.language,
            target_languages=new_list_languages,
            context=TranslationContext(
                context=context,
                messages=[]
            )
        )
