from app.repositories.base import MessageRepository, StoredMessage
from app.repositories.in_memory import (
    InMemoryMessageRepository,
)


async def test_in_memory_repository_stores_and_returns_room_message() -> None:
    storage_message: MessageRepository = InMemoryMessageRepository()

    expected_translations: dict[str, str] = {}
    expected_translations["English"] = "Portuguese -> English + Hello"
    expected_translations["Spanish"] = "Portuguese -> Spanish + Hello"

    expected_message: dict[str, str] = {}
    expected_message["message_id"] = "msg-01"
    expected_message["room"] = "general"
    expected_message["sender_nickname"] = "joao"
    expected_message["sender_language"] = "Portuguese"
    expected_message["original_text"] = "Olá"
    expected_message["sent_at"] = "2026-06-01T12:00:00Z"

    await storage_message.save_message(
        message_id="msg-01",
        room="general",
        sender_nickname="joao",
        sender_language="Portuguese",
        original_text="Olá",
        translations=expected_translations,
        sent_at="2026-06-01T12:00:00Z",
    )

    result = await storage_message.get_messages(room="general")

    assert len(result) == 1
    message: StoredMessage = result[0]

    assert message.message_id == expected_message["message_id"]
    assert message.room == expected_message["room"]
    assert message.sender_nickname == expected_message["sender_nickname"]
    assert message.sender_language == expected_message["sender_language"]
    assert message.original_text == expected_message["original_text"]
    assert message.sent_at == expected_message["sent_at"]

    result_message = message.translations
    assert result_message["English"] == expected_translations["English"]
    assert result_message["Spanish"] == expected_translations["Spanish"]


async def test_in_memory_repository_returns_only_messages_from_requested_room() -> None:
    storage_message: MessageRepository = InMemoryMessageRepository()

    expected_translations: dict[str, str] = {}
    expected_translations["English"] = "Portuguese -> English + Hello"
    expected_translations["Spanish"] = "Portuguese -> Spanish + Hello"

    expected_message: dict[str, str] = {}
    expected_message["message_id"] = "msg-01"
    expected_message["room"] = "general"
    expected_message["sender_nickname"] = "joao"
    expected_message["sender_language"] = "Portuguese"
    expected_message["original_text"] = "Olá"
    expected_message["sent_at"] = "2026-06-01T12:00:00Z"

    await storage_message.save_message(
        message_id="msg-01",
        room="general",
        sender_nickname="joao",
        sender_language="Portuguese",
        original_text="Olá",
        translations=expected_translations,
        sent_at="2026-06-01T12:00:00Z",
    )

    await storage_message.save_message(
        message_id="msg-02",
        room="private",
        sender_nickname="maria",
        sender_language="Portuguese",
        original_text="Olá novamente",
        translations=expected_translations,
        sent_at="2026-06-01T12:00:00Z",
    )

    result = await storage_message.get_messages(room="general")

    assert len(result) == 1
    message: StoredMessage = result[0]

    assert message.message_id == expected_message["message_id"]
    assert message.room == expected_message["room"]
    assert message.sender_nickname == expected_message["sender_nickname"]
    assert message.sender_language == expected_message["sender_language"]
    assert message.original_text == expected_message["original_text"]
    assert message.sent_at == expected_message["sent_at"]

    result_message = message.translations
    assert result_message["English"] == expected_translations["English"]
    assert result_message["Spanish"] == expected_translations["Spanish"]


async def test_in_memory_repository_returns_messages_in_saved_order() -> None:
    storage_message: MessageRepository = InMemoryMessageRepository()

    expected_translations: dict[str, str] = {}
    expected_translations["English"] = "Portuguese -> English + Hello"
    expected_translations["Spanish"] = "Portuguese -> Spanish + Hello"

    expected_message: dict[str, str] = {}
    expected_message["message_id"] = "msg-01"
    expected_message["room"] = "general"
    expected_message["sender_nickname"] = "joao"
    expected_message["sender_language"] = "Portuguese"
    expected_message["original_text"] = "Olá"
    expected_message["sent_at"] = "2026-06-01T12:00:00Z"

    await storage_message.save_message(
        message_id="msg-01",
        room="general",
        sender_nickname="joao",
        sender_language="Portuguese",
        original_text="Olá",
        translations=expected_translations,
        sent_at="2026-06-01T12:00:00Z",
    )

    await storage_message.save_message(
        message_id="msg-02",
        room="general",
        sender_nickname="maria",
        sender_language="Portuguese",
        original_text="Olá novamente",
        translations=expected_translations,
        sent_at="2026-06-01T12:00:00Z",
    )

    result = await storage_message.get_messages(room="general")

    assert len(result) == 2
    assert result[0].message_id == "msg-01"
    assert result[1].message_id == "msg-02"


async def test_in_memory_repository_returns_recent_messages() -> None:
    storage_message: MessageRepository = InMemoryMessageRepository()

    expected_translations: dict[str, str] = {}
    expected_translations["English"] = "Portuguese -> English + Hello"
    expected_translations["Spanish"] = "Portuguese -> Spanish + Hello"

    for _i in range(0, 11):
        await storage_message.save_message(
            message_id=f"msg-0{_i}",
            room="general",
            sender_nickname="joao",
            sender_language="Portuguese",
            original_text="Olá",
            translations=expected_translations,
            sent_at="2026-06-01T12:00:00Z",
        )

    result = await storage_message.get_recent_messages(room="general", number_of_messages=5)

    assert len(result) == 5
    assert result[0].message_id == "msg-06"
    assert result[1].message_id == "msg-07"
    assert result[2].message_id == "msg-08"
    assert result[3].message_id == "msg-09"
    assert result[4].message_id == "msg-010"


async def test_in_memory_repository_returns_all_messages_when_limit_exceeds_history() -> None:
    storage_message: MessageRepository = InMemoryMessageRepository()

    expected_translations: dict[str, str] = {}
    expected_translations["English"] = "Portuguese -> English + Hello"
    expected_translations["Spanish"] = "Portuguese -> Spanish + Hello"

    for _i in range(0, 2):
        await storage_message.save_message(
            message_id=f"msg-0{_i}",
            room="general",
            sender_nickname="joao",
            sender_language="Portuguese",
            original_text="Olá",
            translations=expected_translations,
            sent_at="2026-06-01T12:00:00Z",
        )

    result = await storage_message.get_recent_messages(room="general", number_of_messages=5)

    assert len(result) == 2
    assert result[0].message_id == "msg-00"
    assert result[1].message_id == "msg-01"


async def test_in_memory_repository_returns_empty_list_when_recent_limit_is_zero() -> None:
    storage_message: MessageRepository = InMemoryMessageRepository()

    expected_translations: dict[str, str] = {}
    expected_translations["English"] = "Portuguese -> English + Hello"
    expected_translations["Spanish"] = "Portuguese -> Spanish + Hello"

    for _i in range(0, 2):
        await storage_message.save_message(
            message_id=f"msg-0{_i}",
            room="general",
            sender_nickname="joao",
            sender_language="Portuguese",
            original_text="Olá",
            translations=expected_translations,
            sent_at="2026-06-01T12:00:00Z",
        )

    result = await storage_message.get_recent_messages(room="general", number_of_messages=0)

    assert result == []
