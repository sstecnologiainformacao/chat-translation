export const MAX_MESSAGE_LENGTH = 2000;

export type ClientRoomMessage = {
  type: "room_message";
  room: "general";
  text: string;
};

export type ClientPrivateMessage = {
  type: "private_message";
  recipient_nickname: string;
  text: string;
};

export type ClientTypingMessage = {
  type: "typing";
  recipient_nickname: string | null;
  is_typing: boolean;
};

export type ClientMessage =
  ClientRoomMessage | ClientPrivateMessage | ClientTypingMessage;

export type ServerRoomMessage = {
  type: "room_message";
  message_id: string;
  room: "general";
  sender_nickname: string;
  sender_language: string;
  original_text: string;
  translations: Record<string, string>;
  sent_at: string;
};

export type ServerRoomTranslationUpdateMessage = {
  type: "room_translation_update";
  message_id: string;
  room: "general";
  translations: Record<string, string>;
  translation_status: "completed" | "failed";
};

export type ServerPrivateMessage = {
  type: "private_message";
  message_id: string;
  sender_nickname: string;
  sender_language: string;
  recipient_nickname: string;
  original_text: string;
  translations: Record<string, string>;
  sent_at: string;
};

export type ServerSystemEventMessage = {
  type: "system_event";
  event: "user_joined" | "user_left";
  room: "general";
  nickname: string;
  language?: string | null;
};

export type RoomParticipant = {
  nickname: string;
  language: string;
};

export type ServerRoomPresenceMessage = {
  type: "room_presence";
  room: "general";
  users: RoomParticipant[];
};

export type ServerTypingMessage = {
  type: "typing";
  nickname: string;
  recipient_nickname: string | null;
  is_typing: boolean;
};

export type ServerErrorMessage = {
  type: "error";
  reason:
    | "empty_message"
    | "malformed_payload"
    | "recipient_not_found"
    | "translation_failed"
    | "internal_error";
};

export type RoomHistoryItem = {
  message_id: string;
  sender_nickname: string;
  sender_language: string;
  original_text: string;
  translations: Record<string, string>;
  sent_at: string;
};

export type ServerRoomHistoryMessage = {
  type: "room_history";
  room: "general";
  messages: RoomHistoryItem[];
};

export type ServerMessage =
  | ServerRoomMessage
  | ServerRoomTranslationUpdateMessage
  | ServerPrivateMessage
  | ServerRoomPresenceMessage
  | ServerTypingMessage
  | ServerSystemEventMessage
  | ServerErrorMessage
  | ServerRoomHistoryMessage;
