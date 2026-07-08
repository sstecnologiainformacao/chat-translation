import pytest
from pydantic import ValidationError

from app.schemas.messages import (
    ClientPrivateMessage,
    ClientRoomMessage,
    ServerErrorMessage,
    ServerPrivateMessage,
    ServerRoomMessage,
    ServerSystemEventMessage,
)


def test_client_room_message_default_to_general_room() -> None:
    message = ClientRoomMessage(text="Hello")

    assert message.type == "room_message"
    assert message.room == "general"
    assert message.text == "Hello"


def test_client_room_message_rejects_empty_text() -> None:
    with pytest.raises(ValidationError):
        ClientRoomMessage(text="")


def test_client_room_message_rejects_unknown_room() -> None:
    with pytest.raises(ValidationError):
        ClientRoomMessage.model_validate({"room": "random", "text": "Hello"})


def test_client_private_message_has_recipient_nickname() -> None:
    message = ClientPrivateMessage(recipient_nickname="maria", text="Hello")

    assert message.type == "private_message"
    assert message.recipient_nickname == "maria"
    assert message.text == "Hello"


def test_client_private_message_rejects_empty_recipient() -> None:
    with pytest.raises(ValidationError):
        ClientPrivateMessage(recipient_nickname="", text="Hello")


def test_server_room_message_defaults_to_empty_translations() -> None:
    message = ServerRoomMessage(
        message_id="msg-1",
        sender_nickname="joao",
        sender_language="Portuguese",
        original_text="Hello",
        sent_at="2026-05-29T12:00:00Z",
    )

    assert message.type == "room_message"
    assert message.room == "general"
    assert message.translations == {}


def test_server_private_message_has_recipient_and_translations() -> None:
    message = ServerPrivateMessage(
        message_id="msg-2",
        sender_nickname="joao",
        sender_language="Portuguese",
        recipient_nickname="maria",
        original_text="Hello",
        translations={"English": "Hello"},
        sent_at="2026-05-29T12:01:00Z",
    )

    assert message.type == "private_message"
    assert message.recipient_nickname == "maria"
    assert message.translations == {"English": "Hello"}


def test_server_system_event_language_is_optional() -> None:
    message = ServerSystemEventMessage(event="user_left", nickname="joao")

    assert message.type == "system_event"
    assert message.event == "user_left"
    assert message.room == "general"
    assert message.language is None


def test_server_error_message_restricts_reason() -> None:
    message = ServerErrorMessage(reason="recipient_not_found")

    assert message.type == "error"
    assert message.reason == "recipient_not_found"

    with pytest.raises(ValidationError):
        ServerErrorMessage.model_validate({"reason": "not_allowed"})
