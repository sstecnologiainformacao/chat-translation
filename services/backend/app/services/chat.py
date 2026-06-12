from typing import Protocol

from app.services.translation.base import TranslationProvider


class WebSocketLike(Protocol):
    async def send_json(self, data: dict[str, object]) -> None:
        pass


class ActiveConnection:
    def __init__(self, ws: WebSocketLike, *, nickname: str, language: str) -> None:
        self.ws = ws
        self.nickname = nickname
        self.language = language


class ConnectionManager:
    def __init__(self, *, max_connections: int = 2) -> None:
        self.max_connections = max_connections
        self._connections: list[ActiveConnection] = []
        self._rooms: dict[str, list[ActiveConnection]] = {}

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
        room_connections = self._rooms.setdefault(room, [])

        if connection not in room_connections:
            room_connections.append(connection)

    async def leave_room(self, connection: ActiveConnection, *, room: str) -> None:
        room_connections = self._rooms.get(room)

        if room_connections is None:
            return
        
        if connection in room_connections:
            room_connections.remove(connection)

    async def broadcast_to_room(
            self,
            room: str,
            message: dict[str, object]
    ) -> None:
        room_connections = self._rooms.get(room, [])

        for connection in room_connections:
            await self.send_to(connection, message)

    def room_connection_count(self, room: str) -> int:
        return len(self._rooms.get(room, []))

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
        room_connections = self._rooms.get(room)
        languages: set[str] = set()

        if room_connections is None:
            return languages

        for connection in room_connections:
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
        
        message: dict[str, object] = {
            "type": "private_message",
            "message_id": message_id,
            "sender_nickname": sender.nickname,
            "sender_language": sender.language,
            "recipient_nickname": recipient.nickname,
            "original_text": text,
            "translations": await self._translate_text(
                sender=sender,
                list_languages=set([recipient.language]),
                text=text
            ),
            "sent_at": sent_at,
        }

        await self._manager.send_to(sender, message)
        await self._manager.send_to(recipient, message)

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

        message: dict[str, object] = {
            "type": "room_message",
            "message_id": message_id,
            "room": room,
            "sender_nickname": sender.nickname,
            "sender_language": sender.language,
            "original_text": text,
            "translations": await self._translate_text(
                sender=sender,
                list_languages=list_languages,
                text=text
            ),
            "sent_at": sent_at,
        }

        await self._manager.broadcast_to_room(room, message)

    def _check_languages_to_translate(self, *, sender: ActiveConnection, room: str) -> set[str]:
        return self._manager.target_languages_room(
            language=sender.language,
            room=room,
        )

    async def _translate_text(
        self,
        *,
        sender: ActiveConnection,
        list_languages: set[str],
        text: str
    ) -> dict[str, str]:
        if list_languages is None or len(list_languages) == 0:
            return {}

        translations: dict[str, str] = {}

        list_languages.discard(sender.language)

        for language in list_languages:
            translations[language] = await self.translator.translate(
            text=text,
            source_language=sender.language,
            target_language=language,
        )

        return translations