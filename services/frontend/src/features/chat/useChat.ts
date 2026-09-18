import { useCallback, useMemo } from "react";

import { buildWebSocketUrl } from "@/lib/api";
import { useWebSocket, type WebSocketStatus } from "@/lib/useWebSocket";
import type {
  RoomHistoryItem,
  RoomParticipant,
  ServerMessage,
  ServerPrivateMessage,
  ServerRoomMessage,
  ServerRoomTranslationUpdateMessage,
} from "@/types/messages";
import { MAX_MESSAGE_LENGTH } from "@/types/messages";

type TranslationStatus = "completed" | "failed" | "pending";
type ConversationKind = "private" | "public";

export type ChatMessage = {
  conversationKind: ConversationKind;
  displayText: string;
  id: string;
  originalText: string;
  recipientNickname: string | null;
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
  sendPrivateMessage: (recipientNickname: string, text: string) => boolean;
  sendPublicMessage: (text: string) => boolean;
  status: WebSocketStatus;
  users: RoomParticipant[];
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

        if (message.type === "private_message") {
          const chatMessage = toChatMessage(
            message,
            preferredLanguage,
            "completed",
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

  const users = useMemo(() => {
    let currentUsers: RoomParticipant[] = [];

    for (const message of envelopes) {
      if (message.type === "room_presence") {
        currentUsers = message.users;
      }
    }

    return currentUsers;
  }, [envelopes]);

  const sendPublicMessage = useCallback(
    (text: string) => {
      const trimmedText = text.trim();

      if (!trimmedText || trimmedText.length > MAX_MESSAGE_LENGTH) {
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

  const sendPrivateMessage = useCallback(
    (recipientNickname: string, text: string) => {
      const trimmedRecipient = recipientNickname.trim();
      const trimmedText = text.trim();

      if (
        !trimmedRecipient ||
        !trimmedText ||
        trimmedText.length > MAX_MESSAGE_LENGTH
      ) {
        return false;
      }

      return sendJson({
        type: "private_message",
        recipient_nickname: trimmedRecipient,
        text: trimmedText,
      });
    },
    [sendJson],
  );

  return {
    closeReason,
    messages,
    sendPrivateMessage,
    sendPublicMessage,
    status,
    users,
  };
}

function toPublicChatMessage(message: ChatMessageState): ChatMessage {
  return {
    conversationKind: message.conversationKind,
    displayText: message.displayText,
    id: message.id,
    originalText: message.originalText,
    recipientNickname: message.recipientNickname,
    senderLanguage: message.senderLanguage,
    senderNickname: message.senderNickname,
    sentAt: message.sentAt,
    translationStatus: message.translationStatus,
  };
}

function toChatMessage(
  message: RoomHistoryItem | ServerPrivateMessage | ServerRoomMessage,
  preferredLanguage: string | null,
  translationStatus: TranslationStatus,
): ChatMessageState {
  return {
    conversationKind: getConversationKind(message),
    displayText: getDisplayText(message, preferredLanguage),
    id: message.message_id,
    originalText: message.original_text,
    recipientNickname:
      "recipient_nickname" in message ? message.recipient_nickname : null,
    senderLanguage: message.sender_language,
    senderNickname: message.sender_nickname,
    sentAt: message.sent_at,
    translations: message.translations,
    translationStatus,
  };
}

function getDisplayText(
  message: RoomHistoryItem | ServerPrivateMessage | ServerRoomMessage,
  preferredLanguage: string | null,
): string {
  if (preferredLanguage !== null) {
    return message.translations[preferredLanguage] ?? message.original_text;
  }

  return Object.values(message.translations)[0] ?? message.original_text;
}

function getConversationKind(
  message: RoomHistoryItem | ServerPrivateMessage | ServerRoomMessage,
): ConversationKind {
  return "recipient_nickname" in message ? "private" : "public";
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
