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

export type ClientMessage = ClientRoomMessage | ClientPrivateMessage;

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
  | ServerPrivateMessage
  | ServerSystemEventMessage
  | ServerErrorMessage
  | ServerRoomHistoryMessage;
