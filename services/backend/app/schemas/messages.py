from typing import Literal

from pydantic import BaseModel, Field

MessageText = str


class ClientRoomMessage(BaseModel):
    type: Literal["room_message"] = "room_message"
    room: Literal["general"] = "general"
    text: MessageText = Field(min_length=1, max_length=2000)


class ClientPrivateMessage(BaseModel):
    type: Literal["private_message"] = "private_message"
    recipient_nickname: str = Field(min_length=1, max_length=40)
    text: MessageText = Field(min_length=1, max_length=2000)


ClientMessage = ClientRoomMessage | ClientPrivateMessage


class ServerRoomMessage(BaseModel):
    type: Literal["room_message"] = "room_message"
    message_id: str
    room: Literal["general"] = "general"
    sender_nickname: str
    sender_language: str
    original_text: str
    translations: dict[str, str] = Field(default_factory=dict)
    sent_at: str


class ServerPrivateMessage(BaseModel):
    type: Literal["private_message"] = "private_message"
    message_id: str
    sender_nickname: str
    sender_language: str
    recipient_nickname: str
    original_text: str
    translations: dict[str, str] = Field(default_factory=dict)
    sent_at: str


class ServerSystemEventMessage(BaseModel):
    type: Literal["system_event"] = "system_event"
    event: Literal["user_joined", "user_left"]
    room: Literal["general"] = "general"
    nickname: str
    language: str | None = None


class ServerErrorMessage(BaseModel):
    type: Literal["error"] = "error"
    reason: Literal[
        "empty_message",
        "malformed_payload",
        "recipient_not_found",
        "translation_failed",
        "internal_error",
    ]


class ServerRoomTranslationUpdateMessage(BaseModel):
    type: Literal["room_translation_update"] = "room_translation_update"
    message_id: str
    room: Literal["general"] = "general"
    translations: dict[str, str] = Field(default_factory=dict)
    translation_status: Literal["completed", "failed"]


ServerMessage = (
    ServerRoomMessage
    | ServerPrivateMessage
    | ServerSystemEventMessage
    | ServerErrorMessage
    | ServerRoomTranslationUpdateMessage
)
