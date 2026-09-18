import { fireEvent, render, screen } from "@testing-library/react";
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
const scrollToDescriptor = Object.getOwnPropertyDescriptor(
  HTMLElement.prototype,
  "scrollTo",
);

describe("MessageList", () => {
  afterEach(() => {
    if (scrollToDescriptor) {
      Object.defineProperty(
        HTMLElement.prototype,
        "scrollTo",
        scrollToDescriptor,
      );
      return;
    }

    Reflect.deleteProperty(HTMLElement.prototype, "scrollTo");
  });

  it("renders an empty state when no messages exist", () => {
    render(
      <MessageList
        conversationKey="general"
        currentNickname="joao"
        messages={[]}
      />,
    );

    expect(screen.getByText("Start the conversation.")).toBeInTheDocument();
  });

  it("renders public chat messages", () => {
    render(
      <MessageList
        conversationKey="general"
        currentNickname="joao"
        messages={[message]}
      />,
    );

    expect(screen.getByText("Hello")).toBeInTheDocument();
    expect(screen.getByText("Original: Ola")).toBeInTheDocument();
  });

  it("renders private chat messages", () => {
    render(
      <MessageList
        conversationKey="maria"
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
    const scrollTo = vi.fn();
    Object.defineProperty(HTMLElement.prototype, "scrollTo", {
      configurable: true,
      value: scrollTo,
    });
    const { rerender } = render(
      <MessageList
        conversationKey="general"
        currentNickname="joao"
        messages={[message]}
      />,
    );
    scrollTo.mockClear();

    rerender(
      <MessageList
        conversationKey="general"
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

    expect(scrollTo).toHaveBeenCalledOnce();
    expect(scrollTo).toHaveBeenCalledWith({
      behavior: "smooth",
      top: 0,
    });
  });

  it("preserves the scroll position and counts messages when reading history", () => {
    const scrollTo = vi.fn();
    Object.defineProperty(HTMLElement.prototype, "scrollTo", {
      configurable: true,
      value: scrollTo,
    });
    const { rerender } = render(
      <MessageList
        conversationKey="general"
        currentNickname="joao"
        messages={[message]}
      />,
    );
    const viewport = screen.getByRole("log", { name: "Messages" });
    Object.defineProperties(viewport, {
      clientHeight: { configurable: true, value: 300 },
      scrollHeight: { configurable: true, value: 1000 },
      scrollTop: { configurable: true, value: 200, writable: true },
    });
    fireEvent.scroll(viewport);
    scrollTo.mockClear();

    rerender(
      <MessageList
        conversationKey="general"
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

    expect(scrollTo).not.toHaveBeenCalled();
    expect(
      screen.getByRole("button", { name: "1 new message" }),
    ).toBeInTheDocument();

    rerender(
      <MessageList
        conversationKey="general"
        currentNickname="joao"
        messages={[
          message,
          { ...message, id: "msg-2" },
          { ...message, id: "msg-3" },
        ]}
      />,
    );

    expect(
      screen.getByRole("button", { name: "2 new messages" }),
    ).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "2 new messages" }));

    expect(scrollTo).toHaveBeenCalledOnce();
    expect(scrollTo).toHaveBeenCalledWith({
      behavior: "smooth",
      top: 1000,
    });
    expect(
      screen.queryByRole("button", { name: /new messages?/i }),
    ).not.toBeInTheDocument();
  });

  it("opens a different conversation at its latest message", () => {
    const scrollTo = vi.fn();
    Object.defineProperty(HTMLElement.prototype, "scrollTo", {
      configurable: true,
      value: scrollTo,
    });
    const { rerender } = render(
      <MessageList
        conversationKey="general"
        currentNickname="joao"
        messages={[message]}
      />,
    );
    scrollTo.mockClear();

    rerender(
      <MessageList
        conversationKey="maria"
        currentNickname="joao"
        messages={[{ ...message, id: "private-1" }]}
      />,
    );

    expect(scrollTo).toHaveBeenCalledOnce();
    expect(scrollTo).toHaveBeenCalledWith({
      behavior: "auto",
      top: 0,
    });
  });
});
