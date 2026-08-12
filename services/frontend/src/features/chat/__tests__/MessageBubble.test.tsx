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
      />,
    );

    expect(screen.getByText("joao")).toBeInTheDocument();
    expect(screen.getByText("Portuguese")).toBeInTheDocument();
    expect(screen.getByText("Hello")).toBeInTheDocument();
    expect(screen.getByText("Original: Ola")).toBeInTheDocument();
  });
});
