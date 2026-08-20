import { renderHook } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { useChat } from "@/features/chat/useChat";
import { useWebSocket } from "@/lib/useWebSocket";
import type { ServerMessage } from "@/types/messages";

vi.mock("@/lib/useWebSocket", () => ({
  useWebSocket: vi.fn(),
}));

const mockedUseWebSocket = vi.mocked(useWebSocket);
const sendJson = vi.fn();

describe("useChat", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    sendJson.mockReturnValue(true);
    mockedUseWebSocket.mockReturnValue({
      closeReason: null,
      messages: [],
      sendJson,
      status: "open",
    });
  });

  it("does not connect when there is no token", () => {
    renderHook(() => useChat(null, "English"));

    expect(mockedUseWebSocket).toHaveBeenCalledWith(null);
  });

  it("connects to the backend WebSocket with the token", () => {
    renderHook(() => useChat("jwt-token", "English"));

    expect(mockedUseWebSocket).toHaveBeenCalledWith(
      "ws://localhost:8000/ws/chat?token=jwt-token",
    );
  });

  it("maps room history and room messages to display messages", () => {
    mockedUseWebSocket.mockReturnValue({
      closeReason: null,
      messages: [
        {
          type: "room_history",
          room: "general",
          messages: [
            {
              message_id: "msg-1",
              original_text: "Ola",
              sender_language: "Portuguese",
              sender_nickname: "joao",
              sent_at: "2026-08-11T12:00:00Z",
              translations: { English: "Hello" },
            },
          ],
        },
        {
          type: "room_message",
          message_id: "msg-2",
          original_text: "I am good",
          room: "general",
          sender_language: "English",
          sender_nickname: "maria",
          sent_at: "2026-08-11T12:01:00Z",
          translations: { Portuguese: "Estou bem" },
        },
      ] satisfies ServerMessage[],
      sendJson,
      status: "open",
    });

    const { result } = renderHook(() => useChat("jwt-token", "English"));

    expect(result.current.messages).toEqual([
      {
        displayText: "Hello",
        id: "msg-1",
        originalText: "Ola",
        senderLanguage: "Portuguese",
        senderNickname: "joao",
        sentAt: "2026-08-11T12:00:00Z",
        translationStatus: "completed",
      },
      {
        displayText: "I am good",
        id: "msg-2",
        originalText: "I am good",
        senderLanguage: "English",
        senderNickname: "maria",
        sentAt: "2026-08-11T12:01:00Z",
        translationStatus: "completed",
      },
    ]);
  });

  it("updates pending room messages when a translation update arrives", () => {
    mockedUseWebSocket.mockReturnValue({
      closeReason: null,
      messages: [
        {
          type: "room_message",
          message_id: "msg-1",
          original_text: "Ola",
          room: "general",
          sender_language: "Portuguese",
          sender_nickname: "joao",
          sent_at: "2026-08-11T12:00:00Z",
          translations: {},
        },
        {
          type: "room_translation_update",
          message_id: "msg-1",
          room: "general",
          translation_status: "completed",
          translations: { English: "Hello" },
        },
      ] satisfies ServerMessage[],
      sendJson,
      status: "open",
    });

    const { result } = renderHook(() => useChat("jwt-token", "English"));

    expect(result.current.messages).toEqual([
      {
        displayText: "Hello",
        id: "msg-1",
        originalText: "Ola",
        senderLanguage: "Portuguese",
        senderNickname: "joao",
        sentAt: "2026-08-11T12:00:00Z",
        translationStatus: "completed",
      },
    ]);
  });

  it("keeps the original text visible while translation is pending", () => {
    mockedUseWebSocket.mockReturnValue({
      closeReason: null,
      messages: [
        {
          type: "room_message",
          message_id: "msg-1",
          original_text: "Ola",
          room: "general",
          sender_language: "Portuguese",
          sender_nickname: "joao",
          sent_at: "2026-08-11T12:00:00Z",
          translations: {},
        },
      ] satisfies ServerMessage[],
      sendJson,
      status: "open",
    });

    const { result } = renderHook(() => useChat("jwt-token", "English"));

    expect(result.current.messages).toEqual([
      {
        displayText: "Ola",
        id: "msg-1",
        originalText: "Ola",
        senderLanguage: "Portuguese",
        senderNickname: "joao",
        sentAt: "2026-08-11T12:00:00Z",
        translationStatus: "pending",
      },
    ]);
  });

  it("sends trimmed public room messages", () => {
    const { result } = renderHook(() => useChat("jwt-token", "English"));

    expect(result.current.sendPublicMessage("  Hello  ")).toBe(true);
    expect(sendJson).toHaveBeenCalledWith({
      type: "room_message",
      room: "general",
      text: "Hello",
    });
  });

  it("does not send empty messages", () => {
    const { result } = renderHook(() => useChat("jwt-token", "English"));

    expect(result.current.sendPublicMessage("   ")).toBe(false);
    expect(sendJson).not.toHaveBeenCalled();
  });
});
