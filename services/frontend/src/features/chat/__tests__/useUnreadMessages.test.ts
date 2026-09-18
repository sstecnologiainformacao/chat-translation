import { renderHook } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import type { ChatMessage } from "@/features/chat/useChat";
import { useUnreadMessages } from "@/features/chat/useUnreadMessages";

const publicMessage: ChatMessage = {
  conversationKind: "public",
  displayText: "Hello",
  id: "public-1",
  originalText: "Hello",
  recipientNickname: null,
  senderLanguage: "English",
  senderNickname: "maria",
  sentAt: "2026-08-11T12:00:00Z",
  translationStatus: "completed",
};

const privateMessage: ChatMessage = {
  ...publicMessage,
  conversationKind: "private",
  id: "private-1",
  recipientNickname: "joao",
};

describe("useUnreadMessages", () => {
  it("counts messages received in inactive conversations", () => {
    const { result, rerender } = renderHook(
      ({ activeConversationKey, messages }) =>
        useUnreadMessages(messages, "joao", activeConversationKey, "session-1"),
      {
        initialProps: {
          activeConversationKey: "general",
          messages: [] as ChatMessage[],
        },
      },
    );

    rerender({
      activeConversationKey: "general",
      messages: [privateMessage],
    });

    expect(result.current).toEqual({ maria: 1 });

    rerender({
      activeConversationKey: "maria",
      messages: [privateMessage, { ...publicMessage, id: "public-2" }],
    });

    expect(result.current).toEqual({ general: 1 });
  });

  it("clears a conversation count when the conversation is opened", () => {
    const { result, rerender } = renderHook(
      ({ activeConversationKey, messages }) =>
        useUnreadMessages(messages, "joao", activeConversationKey, "session-1"),
      {
        initialProps: {
          activeConversationKey: "general",
          messages: [] as ChatMessage[],
        },
      },
    );

    rerender({
      activeConversationKey: "general",
      messages: [privateMessage],
    });
    rerender({
      activeConversationKey: "maria",
      messages: [privateMessage],
    });

    expect(result.current).toEqual({});
  });

  it("ignores own messages and updates to known messages", () => {
    const { result, rerender } = renderHook(
      ({ messages }) =>
        useUnreadMessages(messages, "joao", "maria", "session-1"),
      { initialProps: { messages: [] as ChatMessage[] } },
    );
    const ownMessage: ChatMessage = {
      ...privateMessage,
      id: "private-own",
      recipientNickname: "maria",
      senderNickname: "joao",
    };

    rerender({ messages: [ownMessage] });
    rerender({
      messages: [
        {
          ...ownMessage,
          displayText: "Translated text",
          translationStatus: "completed",
        },
      ],
    });

    expect(result.current).toEqual({});
  });

  it("resets unread state for a different session", () => {
    const { result, rerender } = renderHook(
      ({ messages, sessionKey }) =>
        useUnreadMessages(messages, "joao", "general", sessionKey),
      {
        initialProps: {
          messages: [] as ChatMessage[],
          sessionKey: "session-1" as string | null,
        },
      },
    );

    rerender({ messages: [privateMessage], sessionKey: "session-1" });
    expect(result.current).toEqual({ maria: 1 });

    rerender({ messages: [privateMessage], sessionKey: "session-2" });
    expect(result.current).toEqual({});
  });
});
