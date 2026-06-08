from app.services.chat import ChatService, ConnectionManager


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
        "type": 'system_event',
        "event": "user_joined",
        "room": "general",
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

    await manager.join_room(connection, room="general")

    assert manager.room_connection_count("general") == 1


async def test_leave_room_removes_room_membership() -> None:
    manager = ConnectionManager(max_connections=10)
    ws = DummyWebSocket()
    connection = await manager.connect(ws, nickname="joao", language="Portuguese")
    await manager.join_room(connection, room="general")

    await manager.leave_room(connection, room="general")

    assert manager.room_connection_count("general") == 0


async def test_broadcast_to_room_sends_only_to_room_members() -> None:
    manager = ConnectionManager(max_connections=10)
    ws_joao = DummyWebSocket()
    ws_maria = DummyWebSocket()
    ws_ana = DummyWebSocket()

    joao = await manager.connect(ws_joao, nickname="joao", language="Portuguese")
    maria = await manager.connect(ws_maria, nickname="maria", language="English")
    await manager.connect(ws_ana, nickname="ana", language="Spanish")

    await manager.join_room(joao, room="general")
    await manager.join_room(maria, room="general")

    message: dict[str, object] = {
        "type": "room_message",
        "message_id": "msg-1",
        "room": "general",
        "sender_nickname": "joao",
        "sender_language": "Portuguese",
        "original_text": "Hello",
        "translations": {},
        "sent_at": "2026-06-02T12:00:00Z",
    }

    await manager.broadcast_to_room("general", message)

    assert ws_joao.sent == [message]
    assert ws_maria.sent == [message]
    assert ws_ana.sent == []


async def test_join_public_room_broadcasts_join_event() -> None:
    manager = ConnectionManager(max_connections=10)
    service = ChatService(manager)
    ws_joao = DummyWebSocket()
    ws_maria = DummyWebSocket()

    joao = await manager.connect(ws_joao, nickname="joao", language="Portuguese")
    maria = await manager.connect(ws_maria, nickname="maria", language="English")
    await manager.join_room(maria, room="general")

    await service.join_public_room(joao, room="general")

    expected_message: dict[str, object] = {
        "type": "system_event",
        "event": "user_joined",
        "room": "general",
        "nickname": "joao",
        "language": "Portuguese",
    }

    assert ws_joao.sent == [expected_message]
    assert ws_maria.sent == [expected_message]


async def test_leave_public_room_broadcasts_leave_event_to_remaining_members() -> None:
    manager = ConnectionManager(max_connections=10)
    service = ChatService(manager)
    ws_joao = DummyWebSocket()
    ws_maria = DummyWebSocket()

    joao = await manager.connect(ws_joao, nickname="joao", language="Portuguese")
    maria = await manager.connect(ws_maria, nickname="maria", language="English")
    await manager.join_room(joao, room="general")
    await manager.join_room(maria, room="general")

    await service.leave_public_room(joao, room="general")

    expected_message: dict[str, object] = {
        "type": "system_event",
        "event": "user_left",
        "room": "general",
        "nickname": "joao",
        "language": "Portuguese",
    }

    assert ws_joao.sent == []
    assert ws_maria.sent == [expected_message]


async def test_send_private_message_sends_only_to_sender_and_recipient() -> None:
    manager = ConnectionManager(max_connections=10)
    service = ChatService(manager)
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
        "translations": {},
        "sent_at": "2026-06-03T12:00:00Z",
    }

    assert ws_joao.sent == [expected_message]
    assert ws_maria.sent == [expected_message]
    assert ws_ana.sent == []


async def test_send_private_message_returns_error_when_recipient_is_missing() -> None:
    manager = ConnectionManager(max_connections=10)
    service = ChatService(manager)
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
    service = ChatService(manager)
    ws_joao = DummyWebSocket()
    ws_maria = DummyWebSocket()
    ws_ana = DummyWebSocket()

    joao = await manager.connect(ws_joao, nickname="joao", language="Portuguese")
    maria = await manager.connect(ws_maria, nickname="maria", language="English")
    await manager.connect(ws_ana, nickname="ana", language="Spanish")

    await manager.join_room(joao, room="general")
    await manager.join_room(maria, room="general")

    await service.send_room_message(
        joao,
        room="general",
        text="Hello",
        message_id="msg-1",
        sent_at="2026-06-01T12:00:00Z"
    )

    expected_message: dict[str, object] = {
        "type": "room_message",
        "message_id": "msg-1",
        "room": "general",
        "sender_nickname": "joao",
        "sender_language": "Portuguese",
        "original_text": "Hello",
        "translations":  {},
        "sent_at": "2026-06-01T12:00:00Z",
    }

    assert ws_joao.sent == [expected_message]
    assert ws_maria.sent == [expected_message]
    assert ws_ana.sent == []