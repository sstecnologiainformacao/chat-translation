from app.repositories.base import StoredMessage
from app.repositories.in_memory import InMemoryMessageRepository
from app.services.chat import ChatService, ConnectionManager
from app.services.translation.base import (
    TranslationContext,
    TranslationError,
    TranslationResult,
)
from app.services.translation.fake_translator import FakeTranslator


class FakeTranslatorWithError:
    def __init__(self) -> None: ...

    async def translate(
        self,
        *,
        text: str,
        source_language: str,
        target_languages: set[str],
        context: TranslationContext,
    ) -> TranslationResult:
        raise TranslationError()


class DummyWebSocket:
    def __init__(self) -> None:
        self.sent: list[dict[str, object]] = []

    async def send_json(self, data: dict[str, object]) -> None:
        self.sent.append(data)


async def test_connect_tracks_active_connection() -> None:
    manage = ConnectionManager(max_connections=10)
    ws = DummyWebSocket()

    connection = await manage.connect(ws, nickname="joao", language="Portuguese")

    assert connection.ws is ws
    assert connection.nickname == "joao"
    assert connection.language == "Portuguese"
    assert manage.connection_count() == 1


async def test_disconnect_removes_active_connection() -> None:
    manager = ConnectionManager(max_connections=10)
    ws = DummyWebSocket()
    connection = await manager.connect(ws, nickname="joao", language="Portuguese")

    await manager.disconnect(connection)

    assert manager.connection_count() == 0


async def test_send_to_sends_message_to_one_connection() -> None:
    manager = ConnectionManager(max_connections=10)
    ws = DummyWebSocket()
    connection = await manager.connect(ws, nickname="joao", language="Portuguese")
    message: dict[str, object] = {"type": "error", "reason": "internal_error"}

    await manager.send_to(connection, message)

    assert ws.sent == [message]


async def test_broadcast_sends_message_to_all_connections() -> None:
    manager = ConnectionManager(max_connections=10)
    ws_joao = DummyWebSocket()
    ws_maria = DummyWebSocket()
    await manager.connect(ws_joao, nickname="joao", language="Portuguese")
    await manager.connect(ws_maria, nickname="maria", language="English")
    message: dict[str, object] = {
        "type": "system_event",
        "event": "user_joined",
        "room": "room:general",
        "nickname": "joao",
        "language": "Portuguese",
    }

    await manager.broadcast(message)

    assert ws_joao.sent == [message]
    assert ws_maria.sent == [message]


async def test_join_room_tracks_room_membership() -> None:
    manager = ConnectionManager(max_connections=10)
    ws = DummyWebSocket()
    connection = await manager.connect(ws, nickname="joao", language="Portuguese")

    await manager.join_room(connection, room="room:general")

    assert manager.room_connection_count("room:general") == 1


async def test_leave_room_removes_room_membership() -> None:
    manager = ConnectionManager(max_connections=10)
    ws = DummyWebSocket()
    connection = await manager.connect(ws, nickname="joao", language="Portuguese")
    await manager.join_room(connection, room="room:general")

    await manager.leave_room(connection, room="room:general")

    assert manager.room_connection_count("room:general") == 0


async def test_broadcast_to_room_sends_only_to_room_members() -> None:
    manager = ConnectionManager(max_connections=10)
    ws_joao = DummyWebSocket()
    ws_maria = DummyWebSocket()
    ws_ana = DummyWebSocket()

    joao = await manager.connect(ws_joao, nickname="joao", language="Portuguese")
    maria = await manager.connect(ws_maria, nickname="maria", language="English")
    await manager.connect(ws_ana, nickname="ana", language="Spanish")

    await manager.join_room(joao, room="room:general")
    await manager.join_room(maria, room="room:general")

    message: dict[str, object] = {
        "type": "room_message",
        "message_id": "msg-1",
        "room": "room:general",
        "sender_nickname": "joao",
        "sender_language": "Portuguese",
        "original_text": "Hello",
        "translations": {},
        "sent_at": "2026-06-02T12:00:00Z",
    }

    await manager.broadcast_to_room("room:general", message)

    assert ws_joao.sent == [message]
    assert ws_maria.sent == [message]
    assert ws_ana.sent == []


async def test_find_existing_connection_by_nickname() -> None:
    manager = ConnectionManager(max_connections=10)

    ws_joao = DummyWebSocket()
    ws_maria = DummyWebSocket()

    joao = await manager.connect(ws_joao, nickname="joao", language="Portuguese")
    await manager.connect(ws_maria, nickname="maria", language="Portuguese")

    result = manager.find_by_nickname("joao")

    assert result is not None
    assert result.nickname == "joao"
    assert result is joao


async def test_find_missing_connection_by_nickname() -> None:
    manager = ConnectionManager(max_connections=10)

    ws_maria = DummyWebSocket()

    await manager.connect(ws_maria, nickname="maria", language="Portuguese")

    result = manager.find_by_nickname("joao")

    assert result is None


async def test_find_disconnected_connection_by_nickname() -> None:
    manager = ConnectionManager(max_connections=10)

    ws_joao = DummyWebSocket()
    ws_maria = DummyWebSocket()

    await manager.connect(ws_maria, nickname="maria", language="Portuguese")
    joao = await manager.connect(ws_joao, nickname="joao", language="Portuguese")

    await manager.disconnect(joao)

    result = manager.find_by_nickname("joao")

    assert result is None


async def test_join_public_room_broadcasts_join_event() -> None:
    manager = ConnectionManager(max_connections=10)
    service = ChatService(manager, FakeTranslator(), InMemoryMessageRepository())
    ws_joao = DummyWebSocket()
    ws_maria = DummyWebSocket()

    joao = await manager.connect(ws_joao, nickname="joao", language="Portuguese")
    maria = await manager.connect(ws_maria, nickname="maria", language="English")
    await manager.join_room(maria, room="room:general")

    await service.join_public_room(joao, room="room:general")

    expected_message: dict[str, object] = {
        "type": "system_event",
        "event": "user_joined",
        "room": "room:general",
        "nickname": "joao",
        "language": "Portuguese",
    }

    assert ws_joao.sent == [expected_message]
    assert ws_maria.sent == [expected_message]


async def test_leave_public_room_broadcasts_leave_event_to_remaining_members() -> None:
    manager = ConnectionManager(max_connections=10)
    service = ChatService(manager, FakeTranslator(), InMemoryMessageRepository())
    ws_joao = DummyWebSocket()
    ws_maria = DummyWebSocket()

    joao = await manager.connect(ws_joao, nickname="joao", language="Portuguese")
    maria = await manager.connect(ws_maria, nickname="maria", language="English")
    await manager.join_room(joao, room="room:general")
    await manager.join_room(maria, room="room:general")

    await service.leave_public_room(joao, room="room:general")

    expected_message: dict[str, object] = {
        "type": "system_event",
        "event": "user_left",
        "room": "room:general",
        "nickname": "joao",
        "language": "Portuguese",
    }

    assert ws_joao.sent == []
    assert ws_maria.sent == [expected_message]


async def test_send_private_message_sends_only_to_sender_and_recipient() -> None:
    manager = ConnectionManager(max_connections=10)
    service = ChatService(manager, FakeTranslator(), InMemoryMessageRepository())
    ws_joao = DummyWebSocket()
    ws_maria = DummyWebSocket()
    ws_ana = DummyWebSocket()

    joao = await manager.connect(ws_joao, nickname="joao", language="Portuguese")
    await manager.connect(ws_maria, nickname="maria", language="English")
    await manager.connect(ws_ana, nickname="ana", language="Spanish")

    await service.send_private_message(
        joao,
        recipient_nickname="maria",
        text="Hello",
        message_id="msg-1",
        sent_at="2026-06-03T12:00:00Z",
    )

    expected_message: dict[str, object] = {
        "type": "private_message",
        "message_id": "msg-1",
        "sender_nickname": "joao",
        "sender_language": "Portuguese",
        "recipient_nickname": "maria",
        "original_text": "Hello",
        "translations": {"English": "Portuguese -> English + Hello"},
        "sent_at": "2026-06-03T12:00:00Z",
    }

    assert ws_joao.sent == [expected_message]
    assert ws_maria.sent == [expected_message]
    assert ws_ana.sent == []


async def test_send_private_message_returns_error_when_recipient_is_missing() -> None:
    manager = ConnectionManager(max_connections=10)
    service = ChatService(manager, FakeTranslator(), InMemoryMessageRepository())
    ws_joao = DummyWebSocket()

    joao = await manager.connect(ws_joao, nickname="joao", language="Portuguese")

    await service.send_private_message(
        joao,
        recipient_nickname="maria",
        text="Hello",
        message_id="msg-1",
        sent_at="2026-06-03T12:00:00Z",
    )

    expected_message: dict[str, object] = {
        "type": "error",
        "reason": "recipient_not_found",
    }

    assert ws_joao.sent == [expected_message]


async def test_send_room_message_broadcasts_to_room_members() -> None:
    manager = ConnectionManager(max_connections=10)
    service = ChatService(manager, FakeTranslator(), InMemoryMessageRepository())
    ws_joao = DummyWebSocket()
    ws_maria = DummyWebSocket()
    ws_ana = DummyWebSocket()

    joao = await service.connect(ws_joao, nickname="joao", language="Portuguese")
    maria = await service.connect(ws_maria, nickname="maria", language="English")
    await service.connect(ws_ana, nickname="ana", language="Spanish")

    await service.join_room(joao, room="general")
    await service.join_room(maria, room="general")

    await service.send_room_message(
        joao, text="Hello", message_id="msg-1", sent_at="2026-06-01T12:00:00Z"
    )

    expected_message: dict[str, object] = {
        "type": "room_message",
        "message_id": "msg-1",
        "room": "general",
        "sender_nickname": "joao",
        "sender_language": "Portuguese",
        "original_text": "Hello",
        "translations": {"English": "Portuguese -> English + Hello"},
        "sent_at": "2026-06-01T12:00:00Z",
    }

    assert ws_joao.sent == [expected_message]
    assert ws_maria.sent == [expected_message]
    assert ws_ana.sent == []


async def test_translation_property_after_send_message() -> None:
    manager = ConnectionManager(max_connections=10)
    ws_joao = DummyWebSocket()
    ws_maria = DummyWebSocket()
    ws_ana = DummyWebSocket()
    ws_pedro = DummyWebSocket()
    ws_jonny = DummyWebSocket()

    joao = await manager.connect(ws_joao, nickname="joao", language="Portuguese")
    maria = await manager.connect(ws_maria, nickname="maria", language="English")
    ana = await manager.connect(ws_ana, nickname="ana", language="Spanish")
    pedro = await manager.connect(ws_pedro, nickname="pedro", language="Portuguese")
    jonny = await manager.connect(ws_jonny, nickname="jonny", language="English")

    await manager.join_room(joao, room="room:general")
    await manager.join_room(maria, room="room:general")
    await manager.join_room(ana, room="room:general")
    await manager.join_room(pedro, room="room:general")
    await manager.join_room(jonny, room="room:general")

    languages: set[str] = manager.target_languages_room(
        language=joao.language,
        room="room:general",
    )

    assert languages == {"English", "Spanish"}


async def test_check_languages_to_translate() -> None:
    manager = ConnectionManager(max_connections=10)
    service = ChatService(manager, FakeTranslator(), InMemoryMessageRepository())
    ws_joao = DummyWebSocket()
    ws_maria = DummyWebSocket()
    ws_ana = DummyWebSocket()
    ws_pedro = DummyWebSocket()
    ws_jonny = DummyWebSocket()

    joao = await service.connect(ws_joao, nickname="joao", language="Portuguese")
    maria = await service.connect(ws_maria, nickname="maria", language="English")
    ana = await service.connect(ws_ana, nickname="ana", language="Spanish")
    pedro = await service.connect(ws_pedro, nickname="pedro", language="Portuguese")
    jonny = await service.connect(ws_jonny, nickname="jonny", language="English")

    await service.join_room(joao, room="general")
    await service.join_room(maria, room="general")
    await service.join_room(ana, room="general")
    await service.join_room(pedro, room="general")
    await service.join_room(jonny, room="general")

    await service.send_room_message(
        joao, text="Hello", message_id="msg-1", sent_at="2026-06-01T12:00:00Z"
    )

    expected_translations = {}
    expected_translations["English"] = "Portuguese -> English + Hello"
    expected_translations["Spanish"] = "Portuguese -> Spanish + Hello"

    expected_message: dict[str, object] = {
        "type": "room_message",
        "message_id": "msg-1",
        "room": "general",
        "sender_nickname": "joao",
        "sender_language": "Portuguese",
        "original_text": "Hello",
        "translations": expected_translations,
        "sent_at": "2026-06-01T12:00:00Z",
    }

    assert ws_joao.sent == [expected_message]


async def test_translate_message_when_chat_is_private_different_language() -> None:
    manager = ConnectionManager(max_connections=10)
    service = ChatService(
        manager=manager, translator=FakeTranslator(), repository=InMemoryMessageRepository()
    )

    ws_joao = DummyWebSocket()
    ws_maria = DummyWebSocket()

    joao = await manager.connect(ws_joao, nickname="joao", language="Portuguese")
    maria = await manager.connect(ws_maria, nickname="maria", language="English")

    await manager.join_room(joao, room="private-chat-room-01")
    await manager.join_room(maria, room="private-chat-room-01")

    await service.send_private_message(
        joao,
        recipient_nickname="maria",
        text="Hello",
        message_id="hello-01",
        sent_at="2026-06-11T12:00:00Z",
    )

    expected_message: dict[str, object] = {
        "message_id": "hello-01",
        "original_text": "Hello",
        "recipient_nickname": "maria",
        "sender_language": "Portuguese",
        "sender_nickname": "joao",
        "sent_at": "2026-06-11T12:00:00Z",
        "translations": {"English": "Portuguese -> English + Hello"},
        "type": "private_message",
    }

    assert ws_joao.sent == [expected_message]
    assert ws_maria.sent == [expected_message]


async def test_translate_message_when_chat_is_private_same_language() -> None:
    manager = ConnectionManager(max_connections=10)
    service = ChatService(
        manager=manager, translator=FakeTranslator(), repository=InMemoryMessageRepository()
    )

    ws_joao = DummyWebSocket()
    ws_maria = DummyWebSocket()

    joao = await manager.connect(ws_joao, nickname="joao", language="Portuguese")
    maria = await manager.connect(ws_maria, nickname="maria", language="Portuguese")

    await manager.join_room(joao, room="private-chat-room-01")
    await manager.join_room(maria, room="private-chat-room-01")

    await service.send_private_message(
        joao,
        recipient_nickname="maria",
        text="Ola",
        message_id="ola-01",
        sent_at="2026-06-11T12:00:00Z",
    )

    expected_message: dict[str, object] = {
        "message_id": "ola-01",
        "original_text": "Ola",
        "recipient_nickname": "maria",
        "sender_language": "Portuguese",
        "sender_nickname": "joao",
        "sent_at": "2026-06-11T12:00:00Z",
        "translations": {},
        "type": "private_message",
    }

    assert ws_joao.sent == [expected_message]
    assert ws_maria.sent == [expected_message]


async def test_translate_private_message_but_error() -> None:
    manager = ConnectionManager(max_connections=10)
    service = ChatService(
        manager=manager,
        translator=FakeTranslatorWithError(),
        repository=InMemoryMessageRepository(),
    )

    ws_joao = DummyWebSocket()
    ws_maria = DummyWebSocket()

    joao = await manager.connect(ws_joao, nickname="joao", language="Portuguese")
    maria = await manager.connect(ws_maria, nickname="maria", language="English")

    await manager.join_room(joao, room="private-chat-room-01")
    await manager.join_room(maria, room="private-chat-room-01")

    await service.send_private_message(
        joao,
        recipient_nickname="maria",
        text="Ola",
        message_id="ola-01",
        sent_at="2026-06-11T12:00:00Z",
    )

    expected_message: dict[str, object] = {
        "type": "error",
        "reason": "translation_failed",
    }

    assert ws_joao.sent == [expected_message]
    assert ws_maria.sent == []


async def test_create_public_chat_context_key() -> None:
    manager = ConnectionManager(max_connections=10)
    service = ChatService(
        manager=manager, translator=FakeTranslator(), repository=InMemoryMessageRepository()
    )

    ws_joao = DummyWebSocket()
    ws_maria = DummyWebSocket()
    ws_ana = DummyWebSocket()
    ws_pedro = DummyWebSocket()
    ws_jonny = DummyWebSocket()

    joao = await manager.connect(ws_joao, nickname="joao", language="Portuguese")
    maria = await manager.connect(ws_maria, nickname="maria", language="English")
    ana = await manager.connect(ws_ana, nickname="ana", language="Spanish")
    pedro = await manager.connect(ws_pedro, nickname="pedro", language="Portuguese")
    jonny = await manager.connect(ws_jonny, nickname="jonny", language="English")

    await manager.join_room(joao, room="room:general")
    await manager.join_room(maria, room="room:general")
    await manager.join_room(ana, room="room:general")
    await manager.join_room(pedro, room="room:general")
    await manager.join_room(jonny, room="room:general")

    await service.send_room_message(
        joao, text="Hello", message_id="msg-1", sent_at="2026-06-01T12:00:00Z"
    )


async def test_translate_public_message_but_error() -> None:
    manager = ConnectionManager(max_connections=10)
    service = ChatService(
        manager=manager,
        translator=FakeTranslatorWithError(),
        repository=InMemoryMessageRepository(),
    )

    ws_joao = DummyWebSocket()
    ws_maria = DummyWebSocket()
    ws_ana = DummyWebSocket()
    ws_pedro = DummyWebSocket()
    ws_jonny = DummyWebSocket()

    joao = await manager.connect(ws_joao, nickname="joao", language="Portuguese")
    maria = await manager.connect(ws_maria, nickname="maria", language="English")
    ana = await manager.connect(ws_ana, nickname="ana", language="Spanish")
    pedro = await manager.connect(ws_pedro, nickname="pedro", language="Portuguese")
    jonny = await manager.connect(ws_jonny, nickname="jonny", language="English")

    await manager.join_room(joao, room="room:general")
    await manager.join_room(maria, room="room:general")
    await manager.join_room(ana, room="room:general")
    await manager.join_room(pedro, room="room:general")
    await manager.join_room(jonny, room="room:general")

    await service.send_room_message(
        joao, text="Hello", message_id="msg-1", sent_at="2026-06-01T12:00:00Z"
    )

    expected_message: dict[str, object] = {
        "type": "error",
        "reason": "translation_failed",
    }

    assert ws_joao.sent == [expected_message]
    assert ws_maria.sent == []


async def test_send_room_message_updates_room_context_after_successful_translation() -> None:
    manager = ConnectionManager(max_connections=10)
    service = ChatService(
        manager=manager,
        translator=FakeTranslator(context_update_summary="It's a summary"),
        repository=InMemoryMessageRepository(),
    )

    ws_joao = DummyWebSocket()
    ws_maria = DummyWebSocket()

    joao = await service.connect(ws_joao, nickname="joao", language="Portuguese")
    maria = await service.connect(ws_maria, nickname="maria", language="English")

    await service.join_room(joao, room="general")
    await service.join_room(maria, room="general")

    await service.send_room_message(
        joao, text="Hello", message_id="msg-1", sent_at="2026-06-01T12:00:00Z"
    )

    conversation = manager.get_room(room="room:general")

    assert conversation.context.context == "It's a summary"


async def test_send_room_message_does_not_update_room_context_after_failed_translation() -> None:
    manager = ConnectionManager(max_connections=10)
    conversation = manager.get_room(room="room:general")
    conversation.context.context = "A text to be checked later"

    service = ChatService(
        manager=manager,
        translator=FakeTranslatorWithError(),
        repository=InMemoryMessageRepository(),
    )

    ws_joao = DummyWebSocket()
    ws_maria = DummyWebSocket()

    joao = await service.connect(ws_joao, nickname="joao", language="Portuguese")
    maria = await service.connect(ws_maria, nickname="maria", language="English")

    await service.join_room(joao, room="general")
    await service.join_room(maria, room="general")

    await service.send_room_message(
        joao, text="Hello", message_id="msg-1", sent_at="2026-06-01T12:00:00Z"
    )

    conversation_after_send_message = manager.get_room(room="room:general")

    expected_message: dict[str, object] = {
        "type": "error",
        "reason": "translation_failed",
    }

    assert conversation_after_send_message.context.context == conversation.context.context
    assert ws_joao.sent == [expected_message]
    assert ws_maria.sent == []


async def test_send_room_message_adds_original_message_to_room_context() -> None:
    manager = ConnectionManager(max_connections=10)
    service = ChatService(
        manager=manager,
        translator=FakeTranslator(context_update_summary="It's a summary"),
        repository=InMemoryMessageRepository(),
    )

    ws_joao = DummyWebSocket()
    ws_maria = DummyWebSocket()

    joao = await service.connect(ws_joao, nickname="joao", language="Portuguese")
    maria = await service.connect(ws_maria, nickname="maria", language="English")

    await service.join_room(joao, room="general")
    await service.join_room(maria, room="general")

    await service.send_room_message(
        joao, text="Hello", message_id="msg-1", sent_at="2026-06-01T12:00:00Z"
    )

    conversation = manager.get_room(room="room:general")

    assert len(conversation.context.messages) == 1
    assert conversation.context.messages[0].nickname == "joao"
    assert conversation.context.messages[0].message == "Hello"


async def test_send_room_message_keeps_only_recent_messages_in_room_context() -> None:
    manager = ConnectionManager(max_connections=10)
    service = ChatService(
        manager=manager,
        translator=FakeTranslator(context_update_summary="It's a summary"),
        repository=InMemoryMessageRepository(),
    )

    ws_joao = DummyWebSocket()
    ws_maria = DummyWebSocket()

    joao = await service.connect(ws_joao, nickname="joao", language="Portuguese")
    maria = await service.connect(ws_maria, nickname="maria", language="English")

    await service.join_room(joao, room="general")
    await service.join_room(maria, room="general")

    await service.send_room_message(
        joao, text="Hello 1", message_id="msg-1", sent_at="2026-06-01T12:00:00Z"
    )

    await service.send_room_message(
        joao, text="Hello 2", message_id="msg-2", sent_at="2026-06-01T12:00:00Z"
    )

    await service.send_room_message(
        joao, text="Hello 3", message_id="msg-3", sent_at="2026-06-01T12:00:00Z"
    )

    await service.send_room_message(
        joao, text="Hello 4", message_id="msg-4", sent_at="2026-06-01T12:00:00Z"
    )

    await service.send_room_message(
        joao, text="Hello 5", message_id="msg-5", sent_at="2026-06-01T12:00:00Z"
    )

    await service.send_room_message(
        joao, text="Hello 6", message_id="msg-6", sent_at="2026-06-01T12:00:00Z"
    )

    conversation = manager.get_room(room="room:general")

    assert len(conversation.context.messages) == 5
    assert conversation.context.messages[0].nickname == "joao"
    assert conversation.context.messages[1].nickname == "joao"
    assert conversation.context.messages[2].nickname == "joao"
    assert conversation.context.messages[3].nickname == "joao"
    assert conversation.context.messages[4].nickname == "joao"
    assert conversation.context.messages[0].message == "Hello 2"
    assert conversation.context.messages[4].message == "Hello 6"


async def test_send_room_message_keeps_only_recent_messages_in_memory_repository() -> None:
    manager = ConnectionManager(max_connections=10)
    repository = InMemoryMessageRepository()
    service = ChatService(
        manager=manager,
        translator=FakeTranslator(context_update_summary="It's a summary"),
        repository=repository,
    )

    ws_joao = DummyWebSocket()
    ws_maria = DummyWebSocket()

    joao = await service.connect(ws_joao, nickname="joao", language="Portuguese")
    maria = await service.connect(ws_maria, nickname="maria", language="English")

    await service.join_public_room(joao, room="general")
    await service.join_public_room(maria, room="general")

    await service.send_room_message(
        joao, text="Hello 1", message_id="msg-1", sent_at="2026-06-01T12:00:00Z"
    )

    await service.send_room_message(
        joao, text="Hello 2", message_id="msg-2", sent_at="2026-06-01T12:00:00Z"
    )

    await service.send_room_message(
        joao, text="Hello 3", message_id="msg-3", sent_at="2026-06-01T12:00:00Z"
    )

    await service.send_room_message(
        joao, text="Hello 4", message_id="msg-4", sent_at="2026-06-01T12:00:00Z"
    )

    await service.send_room_message(
        joao, text="Hello 5", message_id="msg-5", sent_at="2026-06-01T12:00:00Z"
    )

    await service.send_room_message(
        joao, text="Hello 6", message_id="msg-6", sent_at="2026-06-01T12:00:00Z"
    )

    in_memory_messages: list[StoredMessage] = await repository.get_recent_messages(
        room="general", number_of_messages=5
    )

    assert len(in_memory_messages) == 5
    assert in_memory_messages[0].message_id == "msg-2"
    assert in_memory_messages[1].message_id == "msg-3"
    assert in_memory_messages[2].message_id == "msg-4"
    assert in_memory_messages[3].message_id == "msg-5"
    assert in_memory_messages[4].message_id == "msg-6"


async def test_send_private_message_keeps_only_recent_messages_in_memory_repository() -> None:
    manager = ConnectionManager(max_connections=10)
    repository = InMemoryMessageRepository()
    service = ChatService(
        manager=manager,
        translator=FakeTranslator(context_update_summary="It's a summary"),
        repository=repository,
    )

    ws_joao = DummyWebSocket()
    ws_maria = DummyWebSocket()

    joao = await service.connect(ws_joao, nickname="joao", language="Portuguese")
    maria = await service.connect(ws_maria, nickname="maria", language="English")

    await service.join_room(joao, room="private:joao:maria")
    await service.join_room(maria, room="private:joao:maria")

    await service.send_private_message(
        joao,
        text="Hello 1",
        message_id="msg-1",
        sent_at="2026-06-01T12:00:00Z",
        recipient_nickname="maria",
    )

    await service.send_private_message(
        joao,
        text="Hello 2",
        message_id="msg-2",
        sent_at="2026-06-01T12:00:00Z",
        recipient_nickname="maria",
    )

    await service.send_private_message(
        joao,
        text="Hello 3",
        message_id="msg-3",
        sent_at="2026-06-01T12:00:00Z",
        recipient_nickname="maria",
    )

    await service.send_private_message(
        joao,
        text="Hello 4",
        message_id="msg-4",
        sent_at="2026-06-01T12:00:00Z",
        recipient_nickname="maria",
    )

    await service.send_private_message(
        joao,
        text="Hello 5",
        message_id="msg-5",
        sent_at="2026-06-01T12:00:00Z",
        recipient_nickname="maria",
    )

    await service.send_private_message(
        joao,
        text="Hello 6",
        message_id="msg-6",
        sent_at="2026-06-01T12:00:00Z",
        recipient_nickname="maria",
    )

    in_memory_messages: list[StoredMessage] = await repository.get_recent_messages(
        room="private:joao:maria", number_of_messages=5
    )

    assert len(in_memory_messages) == 5
    assert in_memory_messages[0].message_id == "msg-2"
    assert in_memory_messages[1].message_id == "msg-3"
    assert in_memory_messages[2].message_id == "msg-4"
    assert in_memory_messages[3].message_id == "msg-5"
    assert in_memory_messages[4].message_id == "msg-6"


async def test_send_private_message_does_not_save_message_when_translation_fails() -> None:
    manager = ConnectionManager(max_connections=10)
    repository = InMemoryMessageRepository()
    service = ChatService(
        manager=manager,
        translator=FakeTranslatorWithError(),
        repository=repository,
    )

    ws_joao = DummyWebSocket()
    ws_maria = DummyWebSocket()

    joao = await service.connect(ws_joao, nickname="joao", language="Portuguese")
    maria = await service.connect(ws_maria, nickname="maria", language="English")

    await service.join_room(joao, room="private:joao:maria")
    await service.join_room(maria, room="private:joao:maria")

    await service.send_private_message(
        joao,
        text="Hello 1",
        message_id="msg-1",
        sent_at="2026-06-01T12:00:00Z",
        recipient_nickname="maria",
    )
    in_memory_messages: list[StoredMessage] = await repository.get_recent_messages(
        room="private:joao:maria", number_of_messages=1
    )

    assert in_memory_messages == []


async def test_send_room_message_does_not_save_message_when_translation_fails() -> None:
    manager = ConnectionManager(max_connections=10)
    repository = InMemoryMessageRepository()
    service = ChatService(
        manager=manager, translator=FakeTranslatorWithError(), repository=repository
    )

    ws_joao = DummyWebSocket()
    ws_maria = DummyWebSocket()
    ws_ana = DummyWebSocket()
    ws_pedro = DummyWebSocket()
    ws_jonny = DummyWebSocket()

    joao = await manager.connect(ws_joao, nickname="joao", language="Portuguese")
    maria = await manager.connect(ws_maria, nickname="maria", language="English")
    ana = await manager.connect(ws_ana, nickname="ana", language="Spanish")
    pedro = await manager.connect(ws_pedro, nickname="pedro", language="Portuguese")
    jonny = await manager.connect(ws_jonny, nickname="jonny", language="English")

    await manager.join_room(joao, room="room:general")
    await manager.join_room(maria, room="room:general")
    await manager.join_room(ana, room="room:general")
    await manager.join_room(pedro, room="room:general")
    await manager.join_room(jonny, room="room:general")

    await service.send_room_message(
        joao, text="Hello", message_id="msg-1", sent_at="2026-06-01T12:00:00Z"
    )

    expected_message: dict[str, object] = {
        "type": "error",
        "reason": "translation_failed",
    }

    in_memory_messages: list[StoredMessage] = await repository.get_recent_messages(
        room="general", number_of_messages=1
    )

    assert ws_joao.sent == [expected_message]
    assert ws_maria.sent == []
    assert in_memory_messages == []


async def test_load_messages_from_repository_when_new_user_join_chat() -> None:
    manager = ConnectionManager(max_connections=10)
    service = ChatService(
        manager=manager,
        translator=FakeTranslator(context_update_summary="It's a summary"),
        repository=InMemoryMessageRepository(),
    )

    ws_joao = DummyWebSocket()
    joao = await service.connect(ws_joao, nickname="joao", language="Portuguese")
    await service.join_room(joao, room="general")

    await service.send_room_message(
        joao, text="Hello", message_id="msg-1", sent_at="2026-06-01T12:00:00Z"
    )

    conversation = manager.get_room(room="room:general")

    assert len(conversation.context.messages) == 1
    assert conversation.context.messages[0].nickname == "joao"
    assert conversation.context.messages[0].message == "Hello"

    ws_maria = DummyWebSocket()
    maria = await service.connect(ws_maria, nickname="maria", language="English")
    await service.join_room(maria, room="general")

    assert ws_maria.sent != []
    assert ws_maria.sent[0]["type"] == "room_history"
    assert ws_maria.sent[0]["room"] == "general"
    assert ws_maria.sent[0]["messages"] != []

    assert isinstance(ws_maria.sent[0]["messages"], list)
    messages: list[dict[str, object]] = ws_maria.sent[0]["messages"]
    message: dict[str, object] = messages[0]

    assert isinstance(message, dict)
    assert message["message_id"] == "msg-1"
    assert message["original_text"] == "Hello"
    assert message["sender_nickname"] == "joao"


async def test_new_joiner_receive_messages_properly_translated() -> None:
    manager = ConnectionManager(max_connections=10)
    repository = InMemoryMessageRepository()
    service = ChatService(
        manager=manager,
        translator=FakeTranslator(context_update_summary="It's a summary"),
        repository=repository,
    )

    ws_joao = DummyWebSocket()
    ws_maria = DummyWebSocket()

    joao = await service.connect(ws_joao, nickname="joao", language="Portuguese")
    maria = await service.connect(ws_maria, nickname="maria", language="English")

    await service.join_room(joao, room="general")
    await service.join_room(maria, room="general")

    await service.send_room_message(
        joao, text="Olá", message_id="msg-1", sent_at="2026-06-01T12:00:00Z"
    )

    await service.send_room_message(
        maria, text="Hello", message_id="msg-2", sent_at="2026-06-01T12:00:00Z"
    )

    ws_jose = DummyWebSocket()
    jose = await service.connect(ws_jose, nickname="jose", language="Spanish")
    await service.join_room(jose, room="general")

    assert ws_jose.sent[0]["type"] == "room_history"
    assert isinstance(ws_jose.sent[0]["messages"], list)
    messages: list[dict[str, object]] = ws_jose.sent[0]["messages"]
    message_joao: dict[str, object] | None = None
    for message in messages:
        if message["message_id"] == "msg-1":
            message_joao = message

    assert message_joao is not None
    assert isinstance(message_joao["translations"], dict)
    translations: dict[str, object] = message_joao["translations"]
    assert "Spanish" in translations
    assert translations["Spanish"] == "Portuguese -> Spanish + Olá"
