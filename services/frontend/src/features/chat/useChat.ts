import { useCallback, useMemo } from "react";

import { buildWebSocketUrl } from "@/lib/api";
import { useWebSocket, type WebSocketStatus } from "@/lib/useWebSocket";
import type {
  RoomHistoryItem,
  ServerMessage,
  ServerRoomMessage,
} from "@/types/messages";

export type ChatMessage = {
  displayText: string;
  id: string;
  originalText: string;
  senderLanguage: string;
  senderNickname: string;
  sentAt: string;
};

export type UseChatResult = {
  closeReason: string | null;
  messages: ChatMessage[];
  sendPublicMessage: (text: string) => boolean;
  status: WebSocketStatus;
};

export function useChat(
  token: string | null,
  preferredLanguage: string | null,
): UseChatResult {
  const socketUrl =
    token === null ? null : buildWebSocketUrl("/ws/chat", token);
  const {
    closeReason,
    messages: envelopes,
    sendJson,
    status,
  } = useWebSocket<ServerMessage>(socketUrl);

  const messages = useMemo(
    () =>
      envelopes.flatMap((message) => {
        if (message.type === "room_history") {
          return message.messages.map((historyItem) =>
            toChatMessage(historyItem, preferredLanguage),
          );
        }

        if (message.type === "room_message") {
          return [toChatMessage(message, preferredLanguage)];
        }

        return [];
      }),
    [envelopes, preferredLanguage],
  );

  const sendPublicMessage = useCallback(
    (text: string) => {
      const trimmedText = text.trim();

      if (!trimmedText) {
        return false;
      }

      return sendJson({
        type: "room_message",
        room: "general",
        text: trimmedText,
      });
    },
    [sendJson],
  );

  return {
    closeReason,
    messages,
    sendPublicMessage,
    status,
  };
}

function toChatMessage(
  message: RoomHistoryItem | ServerRoomMessage,
  preferredLanguage: string | null,
): ChatMessage {
  return {
    displayText: getDisplayText(message, preferredLanguage),
    id: message.message_id,
    originalText: message.original_text,
    senderLanguage: message.sender_language,
    senderNickname: message.sender_nickname,
    sentAt: message.sent_at,
  };
}

function getDisplayText(
  message: RoomHistoryItem | ServerRoomMessage,
  preferredLanguage: string | null,
): string {
  if (preferredLanguage !== null) {
    return message.translations[preferredLanguage] ?? message.original_text;
  }

  return Object.values(message.translations)[0] ?? message.original_text;
}
