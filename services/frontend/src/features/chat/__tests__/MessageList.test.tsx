import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { MessageList } from "@/features/chat/MessageList";
import type { ChatMessage } from "@/features/chat/useChat";

const message: ChatMessage = {
  conversationKind: "public",
  displayText: "Hello",
  id: "msg-1",
  originalText: "Ola",
  recipientNickname: null,
  senderLanguage: "Portuguese",
  senderNickname: "joao",
  sentAt: "2026-08-11T12:00:00Z",
  translationStatus: "completed",
};
const scrollIntoViewDescriptor = Object.getOwnPropertyDescriptor(
  Element.prototype,
  "scrollIntoView",
);

describe("MessageList", () => {
  afterEach(() => {
    if (scrollIntoViewDescriptor) {
      Object.defineProperty(
        Element.prototype,
        "scrollIntoView",
        scrollIntoViewDescriptor,
      );
      return;
    }

    Reflect.deleteProperty(Element.prototype, "scrollIntoView");
  });

  it("renders an empty state when no messages exist", () => {
    render(<MessageList currentNickname="joao" messages={[]} />);

    expect(screen.getByText("Start the conversation.")).toBeInTheDocument();
  });

  it("renders public chat messages", () => {
    render(<MessageList currentNickname="joao" messages={[message]} />);

    expect(screen.getByText("Hello")).toBeInTheDocument();
    expect(screen.getByText("Original: Ola")).toBeInTheDocument();
  });

  it("renders private chat messages", () => {
    render(
      <MessageList
        currentNickname="joao"
        messages={[
          {
            ...message,
            conversationKind: "private",
            recipientNickname: "maria",
          },
        ]}
      />,
    );

    expect(screen.getByText("Private to maria")).toBeInTheDocument();
  });

  it("scrolls to the bottom when a new message arrives", () => {
    const scrollIntoView = vi.fn();
    Object.defineProperty(Element.prototype, "scrollIntoView", {
      configurable: true,
      value: scrollIntoView,
    });
    const { rerender } = render(
      <MessageList currentNickname="joao" messages={[message]} />,
    );
    scrollIntoView.mockClear();

    rerender(
      <MessageList
        currentNickname="joao"
        messages={[
          message,
          {
            ...message,
            displayText: "Welcome",
            id: "msg-2",
            originalText: "Bem-vindo",
          },
        ]}
      />,
    );

    expect(scrollIntoView).toHaveBeenCalledOnce();
    expect(scrollIntoView).toHaveBeenCalledWith({
      behavior: "smooth",
      block: "end",
    });
  });
});
