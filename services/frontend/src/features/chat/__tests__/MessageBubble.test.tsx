import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { MessageBubble } from "@/features/chat/MessageBubble";

describe("MessageBubble", () => {
  it("renders translated and original message content", () => {
    render(
      <MessageBubble
        author="joao"
        language="Portuguese"
        originalText="Ola"
        text="Hello"
        translationStatus="completed"
      />,
    );

    expect(screen.getByText("joao")).toBeInTheDocument();
    expect(screen.getByText("Portuguese")).toBeInTheDocument();
    expect(screen.getByText("Hello")).toBeInTheDocument();
    expect(screen.getByText("Original: Ola")).toBeInTheDocument();
  });

  it("renders a translation pending state", () => {
    render(
      <MessageBubble
        author="joao"
        language="Portuguese"
        originalText="Ola"
        text="Ola"
        translationStatus="pending"
      />,
    );

    expect(screen.getByLabelText("Translation pending")).toBeInTheDocument();
  });

  it("renders a translation failure state", () => {
    render(
      <MessageBubble
        author="joao"
        language="Portuguese"
        originalText="Ola"
        text="Ola"
        translationStatus="failed"
      />,
    );

    expect(screen.getByText("Translation unavailable.")).toBeInTheDocument();
  });
});
