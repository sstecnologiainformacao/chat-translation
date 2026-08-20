import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { MessageList } from "@/features/chat/MessageList";
import type { ChatMessage } from "@/features/chat/useChat";

const message: ChatMessage = {
  displayText: "Hello",
  id: "msg-1",
  originalText: "Ola",
  senderLanguage: "Portuguese",
  senderNickname: "joao",
  sentAt: "2026-08-11T12:00:00Z",
  translationStatus: "completed",
};

describe("MessageList", () => {
  it("renders an empty state when no messages exist", () => {
    render(<MessageList messages={[]} />);

    expect(screen.getByText("No messages yet.")).toBeInTheDocument();
  });

  it("renders public chat messages", () => {
    render(<MessageList messages={[message]} />);

    expect(screen.getByText("Hello")).toBeInTheDocument();
    expect(screen.getByText("Original: Ola")).toBeInTheDocument();
  });
});
