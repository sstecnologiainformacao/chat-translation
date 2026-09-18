import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { TypingIndicator } from "@/features/chat/TypingIndicator";

describe("TypingIndicator", () => {
  it("reserves space without announcing inactive typing", () => {
    const { container } = render(<TypingIndicator nicknames={[]} />);

    expect(container.firstChild).toHaveClass("min-h-5");
    expect(screen.queryByRole("status")).not.toBeInTheDocument();
  });

  it("describes one or more typing participants", () => {
    const { rerender } = render(<TypingIndicator nicknames={["maria"]} />);
    expect(screen.getByRole("status")).toHaveTextContent("maria is typing...");

    rerender(<TypingIndicator nicknames={["maria", "ana"]} />);
    expect(screen.getByRole("status")).toHaveTextContent(
      "maria and ana are typing...",
    );

    rerender(<TypingIndicator nicknames={["maria", "ana", "pedro"]} />);
    expect(screen.getByRole("status")).toHaveTextContent(
      "maria and 2 others are typing...",
    );
  });
});
