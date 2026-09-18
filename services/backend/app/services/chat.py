from time import perf_counter_ns
from typing import Protocol

from starlette.websockets import WebSocketDisconnect

from app.repositories.base import MessageRepository, StoredMessage
from app.services.translation.base import (
    Message,
    TranslationContext,
    TranslationError,
    TranslationProvider,
    TranslationResult,
)
from app.services.translation.diagnostics import (
    TranslationDiagnostics,
    elapsed_ms,
    emit_translation_performance,
)


class WebSocketLike(Protocol):
    async def send_json(self, data: dict[str, object]) -> None:
        pass


class ActiveConnection:
    def __init__(self, ws: WebSocketLike, *, nickname: str, language: str) -> None:
        self.ws = ws
        self.nickname = nickname
        self.language = language


class ConnectionLimitReachedError(Exception):
    "The room is full at this moment. Try again later"


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
        if len(self._connections) >= self.max_connections:
            raise ConnectionLimitReachedError()

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

    async def broadcast_to_room(
        self,
        room: str,
        message: dict[str, object],
        *,
        exclude: ActiveConnection | None = None,
    ) -> None:
        conversation: Conversation = self._rooms.get(room, Conversation(key=room))

        for connection in tuple(conversation.connections):
            if connection is exclude:
                continue
            try:
                await self.send_to(connection, message)
            except (RuntimeError, WebSocketDisconnect):
                await self.disconnect(connection)

    def room_connection_count(self, room: str) -> int:
        conversation: Conversation = self._rooms.get(room, Conversation(key=room))
        return len(conversation.connections)

    def room_participants(self, room: str) -> list[dict[str, str]]:
        conversation = self._rooms.get(room)
        if conversation is None:
            return []

        participants = {
            connection.nickname: {
                "nickname": connection.nickname,
                "language": connection.language,
            }
            for connection in conversation.connections
        }
        return sorted(participants.values(), key=lambda item: item["nickname"].casefold())

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
        message_received_ns: int | None = None,
        validation_ms: float = 0.0,
    ) -> None:
        recipient = self._manager.find_by_nickname(recipient_nickname)

        if recipient is None:
            error_message: dict[str, object] = {
                "type": "error",
                "reason": "recipient_not_found",
            }

            await self._manager.send_to(sender, error_message)
            return

        received_ns = message_received_ns or perf_counter_ns()
        sorted_users_nicks = sorted([sender.nickname, recipient_nickname])
        room = f"private:{':'.join(sorted_users_nicks)}"
        conversation: Conversation = self._get_room(room=room)
        diagnostics = TranslationDiagnostics(
            room_id="private",
            message_id=message_id,
            source_language=sender.language,
            target_language_count=1,
            room_connection_count=2,
            message_received_ns=received_ns,
            operation_type="private_message",
            validation_ms=validation_ms,
        )
        diagnostics.recent_context_message_count = len(conversation.context.messages)
        diagnostics.context_summary_character_count = len(conversation.context.context)
        diagnostics.recent_context_character_count = sum(
            len(item.nickname) + len(item.message) for item in conversation.context.messages
        )
        current_stage = "translation"
        translation_started_ns = perf_counter_ns()

        try:
            if conversation is not None:
                translations = await self._translate_text(
                    sender=sender,
                    list_languages=set([recipient.language]),
                    text=text,
                    context=conversation.context,
                    diagnostics=diagnostics,
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
                current_stage = "translation_broadcast"
                translation_broadcast_started_ns = perf_counter_ns()
                try:
                    await self._manager.send_to(sender, message)
                    await self._manager.send_to(recipient, message)
                finally:
                    diagnostics.translation_broadcast_ms = elapsed_ms(
                        translation_broadcast_started_ns
                    )
                translation_broadcast_completed_ns = perf_counter_ns()
                diagnostics.message_to_translation_update_ms = elapsed_ms(
                    received_ns,
                    translation_broadcast_completed_ns,
                )
                diagnostics.translation_pipeline_ms = elapsed_ms(
                    translation_started_ns,
                    translation_broadcast_completed_ns,
                )
                diagnostics.status = "skipped" if translations is None else "success"

                current_stage = "repository_save"
                repository_save_started_ns = perf_counter_ns()
                try:
                    await self.repository.save_message(
                        message_id=message_id,
                        room=room,
                        sender_nickname=sender.nickname,
                        sender_language=sender.language,
                        original_text=text,
                        translations=result_translation,
                        sent_at=sent_at,
                    )
                finally:
                    diagnostics.repository_save_ms = elapsed_ms(repository_save_started_ns)
            else:
                raise TranslationError
        except TranslationError as error:
            if diagnostics.failure_stage is None:
                diagnostics.mark_failed(stage=current_stage, error=error)
            error_broadcast_started_ns = perf_counter_ns()
            try:
                await self._manager.send_to(
                    sender,
                    {
                        "type": "error",
                        "reason": "translation_failed",
                    },
                )
            finally:
                error_broadcast_completed_ns = perf_counter_ns()
                diagnostics.translation_broadcast_ms = elapsed_ms(
                    error_broadcast_started_ns,
                    error_broadcast_completed_ns,
                )
                diagnostics.message_to_translation_update_ms = elapsed_ms(
                    received_ns,
                    error_broadcast_completed_ns,
                )
                diagnostics.translation_pipeline_ms = elapsed_ms(
                    translation_started_ns,
                    error_broadcast_completed_ns,
                )
            return
        except Exception as error:
            diagnostics.mark_failed(stage=current_stage, error=error)
            raise
        finally:
            diagnostics.handler_total_ms = elapsed_ms(received_ns)
            emit_translation_performance(diagnostics)

    async def send_typing_status(
        self,
        sender: ActiveConnection,
        *,
        recipient_nickname: str | None,
        is_typing: bool,
    ) -> None:
        message: dict[str, object] = {
            "type": "typing",
            "nickname": sender.nickname,
            "recipient_nickname": recipient_nickname,
            "is_typing": is_typing,
        }

        if recipient_nickname is None:
            await self._manager.broadcast_to_room(
                self._get_key_room_general(),
                message,
                exclude=sender,
            )
            return

        recipient = self._manager.find_by_nickname(recipient_nickname)
        if recipient is not None:
            await self._manager.send_to(recipient, message)

    async def send_room_message(
        self,
        sender: ActiveConnection,
        *,
        text: str,
        message_id: str,
        sent_at: str,
        message_received_ns: int | None = None,
        validation_ms: float = 0.0,
    ) -> None:
        received_ns = message_received_ns or perf_counter_ns()
        room_key = self._get_key_room_general()
        list_languages: set[str] = self._check_languages_to_translate(sender=sender, room=room_key)

        conversation: Conversation | None = self._get_room(room=room_key)
        diagnostics = TranslationDiagnostics(
            room_id="general",
            message_id=message_id,
            source_language=sender.language,
            target_language_count=len(list_languages),
            room_connection_count=self._manager.room_connection_count(room_key),
            message_received_ns=received_ns,
            validation_ms=validation_ms,
        )
        current_stage = "message_preparation"
        translation_started_ns: int | None = None

        try:
            if conversation is not None:
                message: dict[str, object] = {
                    "type": "room_message",
                    "message_id": message_id,
                    "room": "general",
                    "sender_nickname": sender.nickname,
                    "sender_language": sender.language,
                    "original_text": text,
                    "translations": {},
                    "sent_at": sent_at,
                }

                original_message = Message(message=text, nickname=sender.nickname)
                conversation.add_message(message=original_message)
                diagnostics.recent_context_message_count = len(conversation.context.messages)
                diagnostics.context_summary_character_count = len(conversation.context.context)
                diagnostics.recent_context_character_count = sum(
                    len(item.nickname) + len(item.message) for item in conversation.context.messages
                )

                current_stage = "original_broadcast"
                original_broadcast_started_ns = perf_counter_ns()
                try:
                    await self._manager.broadcast_to_room(room_key, message)
                finally:
                    diagnostics.original_broadcast_ms = elapsed_ms(original_broadcast_started_ns)

                current_stage = "translation"
                translation_started_ns = perf_counter_ns()
                translations_result: TranslationResult | None = await self._translate_text(
                    sender=sender,
                    list_languages=list_languages,
                    text=text,
                    context=conversation.context,
                    diagnostics=diagnostics,
                )

                if (
                    translations_result is not None
                    and translations_result.context_update is not None
                ):
                    conversation.update_context(
                        new_context=translations_result.context_update.summary
                    )

                translations_dict = getattr(translations_result, "translations", {})

                message_translated: dict[str, object] = {
                    "type": "room_translation_update",
                    "message_id": message_id,
                    "room": "general",
                    "sender_nickname": sender.nickname,
                    "sender_language": sender.language,
                    "original_text": text,
                    "translations": translations_dict,
                    "translation_status": "completed",
                    "sent_at": sent_at,
                }

                current_stage = "translation_broadcast"
                translation_broadcast_started_ns = perf_counter_ns()
                try:
                    await self._manager.broadcast_to_room(room_key, message_translated)
                finally:
                    diagnostics.translation_broadcast_ms = elapsed_ms(
                        translation_broadcast_started_ns
                    )
                translation_broadcast_completed_ns = perf_counter_ns()
                diagnostics.message_to_translation_update_ms = elapsed_ms(
                    received_ns,
                    translation_broadcast_completed_ns,
                )
                diagnostics.translation_pipeline_ms = elapsed_ms(
                    translation_started_ns,
                    translation_broadcast_completed_ns,
                )
                diagnostics.status = "skipped" if translations_result is None else "success"

                current_stage = "repository_save"
                repository_save_started_ns = perf_counter_ns()
                try:
                    await self.repository.save_message(
                        message_id=message_id,
                        room="general",
                        sender_nickname=sender.nickname,
                        sender_language=sender.language,
                        original_text=text,
                        translations=translations_dict,
                        sent_at=sent_at,
                    )
                finally:
                    diagnostics.repository_save_ms = elapsed_ms(repository_save_started_ns)
        except TranslationError as error:
            if diagnostics.failure_stage is None:
                diagnostics.mark_failed(stage=current_stage, error=error)
            message_failed: dict[str, object] = {
                "type": "room_translation_update",
                "message_id": message_id,
                "room": "general",
                "sender_nickname": sender.nickname,
                "sender_language": sender.language,
                "original_text": text,
                "translations": {},
                "translation_status": "failed",
                "sent_at": sent_at,
            }
            translation_broadcast_started_ns = perf_counter_ns()
            try:
                await self._manager.broadcast_to_room(room_key, message_failed)
            except Exception as broadcast_error:
                diagnostics.mark_failed(
                    stage="translation_broadcast",
                    error=broadcast_error,
                )
                raise
            finally:
                translation_broadcast_completed_ns = perf_counter_ns()
                diagnostics.translation_broadcast_ms = elapsed_ms(
                    translation_broadcast_started_ns,
                    translation_broadcast_completed_ns,
                )
                diagnostics.message_to_translation_update_ms = elapsed_ms(
                    received_ns,
                    translation_broadcast_completed_ns,
                )
                if translation_started_ns is not None:
                    diagnostics.translation_pipeline_ms = elapsed_ms(
                        translation_started_ns,
                        translation_broadcast_completed_ns,
                    )
            return
        except Exception as error:
            diagnostics.mark_failed(stage=current_stage, error=error)
            raise
        finally:
            diagnostics.handler_total_ms = elapsed_ms(received_ns)
            emit_translation_performance(diagnostics)

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
        diagnostics: TranslationDiagnostics | None = None,
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
            diagnostics=diagnostics,
        )

    async def _translate_history_message(
        self,
        *,
        message: StoredMessage,
        room: str,
        target_languages: set[str],
        context: TranslationContext,
    ) -> TranslationResult:
        operation_started_ns = perf_counter_ns()
        diagnostics = TranslationDiagnostics(
            room_id=room,
            message_id=message.message_id,
            source_language=message.sender_language,
            target_language_count=len(target_languages),
            room_connection_count=self._manager.room_connection_count(self.build_room_key(room)),
            message_received_ns=operation_started_ns,
            operation_type="history_translation",
            recent_context_message_count=len(context.messages),
            context_summary_character_count=len(context.context),
            recent_context_character_count=sum(
                len(item.nickname) + len(item.message) for item in context.messages
            ),
        )
        try:
            result = await self.translator.translate(
                text=message.original_text,
                source_language=message.sender_language,
                target_languages=target_languages,
                context=context,
                diagnostics=diagnostics,
            )
            diagnostics.status = "success"
            return result
        except Exception as error:
            if diagnostics.failure_stage is None:
                diagnostics.mark_failed(stage="translation", error=error)
            raise
        finally:
            diagnostics.translation_pipeline_ms = elapsed_ms(operation_started_ns)
            diagnostics.handler_total_ms = diagnostics.translation_pipeline_ms
            emit_translation_performance(diagnostics)

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
                        result: TranslationResult | None = await self._translate_history_message(
                            message=message,
                            room=room,
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

    async def broadcast_room_presence(self, *, room: str) -> None:
        room_key = self.build_room_key(room)
        await self._manager.broadcast_to_room(
            room_key,
            {
                "type": "room_presence",
                "room": room,
                "users": self._manager.room_participants(room_key),
            },
        )
