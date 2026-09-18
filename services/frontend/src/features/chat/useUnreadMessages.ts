import { useState } from "react";

import type { ChatMessage } from "@/features/chat/useChat";

export type UnreadMessageCounts = Record<string, number>;

type UnreadMessageTracker = {
  activeConversationKey: string;
  counts: UnreadMessageCounts;
  knownMessageIds: Set<string>;
  sessionKey: string | null;
};

export function useUnreadMessages(
  messages: ChatMessage[],
  currentNickname: string | null,
  activeConversationKey: string,
  sessionKey: string | null,
): UnreadMessageCounts {
  const [tracker, setTracker] = useState<UnreadMessageTracker>(() => ({
    activeConversationKey,
    counts: {},
    knownMessageIds: new Set(messages.map((message) => message.id)),
    sessionKey,
  }));
  const sessionChanged = tracker.sessionKey !== sessionKey;
  const activeConversationChanged =
    tracker.activeConversationKey !== activeConversationKey;
  const newMessages = sessionChanged
    ? []
    : messages.filter((message) => !tracker.knownMessageIds.has(message.id));

  if (sessionChanged || activeConversationChanged || newMessages.length > 0) {
    if (sessionChanged) {
      setTracker({
        activeConversationKey,
        counts: {},
        knownMessageIds: new Set(messages.map((message) => message.id)),
        sessionKey,
      });
    } else {
      const counts = { ...tracker.counts };
      const knownMessageIds = new Set(tracker.knownMessageIds);

      delete counts[activeConversationKey];

      for (const message of newMessages) {
        knownMessageIds.add(message.id);

        if (message.senderNickname === currentNickname) {
          continue;
        }

        const conversationKey = getConversationKey(message, currentNickname);
        if (conversationKey !== activeConversationKey) {
          counts[conversationKey] = (counts[conversationKey] ?? 0) + 1;
        }
      }

      setTracker({
        activeConversationKey,
        counts,
        knownMessageIds,
        sessionKey,
      });
    }
  }

  return sessionChanged ? {} : tracker.counts;
}

function getConversationKey(
  message: ChatMessage,
  currentNickname: string | null,
): string {
  if (message.conversationKind === "public") {
    return "general";
  }

  return message.senderNickname === currentNickname
    ? (message.recipientNickname ?? "general")
    : message.senderNickname;
}
