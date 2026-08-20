import { useCallback, useMemo } from "react";

import { buildWebSocketUrl } from "@/lib/api";
import { useWebSocket, type WebSocketStatus } from "@/lib/useWebSocket";
import type {
  RoomHistoryItem,
  ServerMessage,
  ServerRoomMessage,
  ServerRoomTranslationUpdateMessage,
} from "@/types/messages";

type TranslationStatus = "completed" | "failed" | "pending";

export type ChatMessage = {
  displayText: string;
  id: string;
  originalText: string;
  senderLanguage: string;
  senderNickname: string;
  sentAt: string;
  translationStatus: TranslationStatus;
};

type ChatMessageState = ChatMessage & {
  translations: Record<string, string>;
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
    () => {
      const orderedMessages: ChatMessageState[] = [];
      const messageIndexes = new Map<string, number>();

      for (const message of envelopes) {
        if (message.type === "room_history") {
          for (const historyItem of message.messages) {
            const chatMessage = toChatMessage(
              historyItem,
              preferredLanguage,
              "completed",
            );
            messageIndexes.set(chatMessage.id, orderedMessages.length);
            orderedMessages.push(chatMessage);
          }
          continue;
        }

        if (message.type === "room_message") {
          const chatMessage = toChatMessage(
            message,
            preferredLanguage,
            getInitialTranslationStatus(message, preferredLanguage),
          );
          messageIndexes.set(chatMessage.id, orderedMessages.length);
          orderedMessages.push(chatMessage);
          continue;
        }

        if (message.type === "room_translation_update") {
          const existingIndex = messageIndexes.get(message.message_id);

          if (existingIndex === undefined) {
            continue;
          }

          orderedMessages[existingIndex] = updateChatMessage(
            orderedMessages[existingIndex],
            message,
            preferredLanguage,
          );
        }
      }

      return orderedMessages.map(toPublicChatMessage);
    },
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

function toPublicChatMessage(message: ChatMessageState): ChatMessage {
  return {
    displayText: message.displayText,
    id: message.id,
    originalText: message.originalText,
    senderLanguage: message.senderLanguage,
    senderNickname: message.senderNickname,
    sentAt: message.sentAt,
    translationStatus: message.translationStatus,
  };
}

function toChatMessage(
  message: RoomHistoryItem | ServerRoomMessage,
  preferredLanguage: string | null,
  translationStatus: TranslationStatus,
): ChatMessageState {
  return {
    displayText: getDisplayText(message, preferredLanguage),
    id: message.message_id,
    originalText: message.original_text,
    senderLanguage: message.sender_language,
    senderNickname: message.sender_nickname,
    sentAt: message.sent_at,
    translations: message.translations,
    translationStatus,
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

function getDisplayTextFromParts(
  translations: Record<string, string>,
  originalText: string,
  preferredLanguage: string | null,
): string {
  if (preferredLanguage !== null) {
    return translations[preferredLanguage] ?? originalText;
  }

  return Object.values(translations)[0] ?? originalText;
}

function getInitialTranslationStatus(
  message: ServerRoomMessage,
  preferredLanguage: string | null,
): TranslationStatus {
  if (
    preferredLanguage === null ||
    preferredLanguage === message.sender_language
  ) {
    return "completed";
  }

  if (message.translations[preferredLanguage] !== undefined) {
    return "completed";
  }

  return "pending";
}

function updateChatMessage(
  currentMessage: ChatMessageState,
  update: ServerRoomTranslationUpdateMessage,
  preferredLanguage: string | null,
): ChatMessageState {
  const translations = {
    ...currentMessage.translations,
    ...update.translations,
  };

  return {
    ...currentMessage,
    displayText: getDisplayTextFromParts(
      translations,
      currentMessage.originalText,
      preferredLanguage,
    ),
    translations,
    translationStatus: update.translation_status,
  };
}
