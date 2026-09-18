import { useState } from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { MessageInput } from "@/features/chat/MessageInput";

describe("MessageInput", () => {
  it("notifies text changes and submit actions", async () => {
    const onChange = vi.fn();
    const onSubmit = vi.fn();
    const user = userEvent.setup();

    render(<TestMessageInput onChange={onChange} onSubmit={onSubmit} />);

    await user.type(screen.getByLabelText("Message"), "Hello");

    expect(onChange).toHaveBeenLastCalledWith("Hello");
    await user.click(screen.getByRole("button", { name: "Send message" }));

    expect(onSubmit).toHaveBeenCalledOnce();
  });

  it("submits with Enter", async () => {
    const onSubmit = vi.fn();
    const user = userEvent.setup();

    render(<TestMessageInput onChange={vi.fn()} onSubmit={onSubmit} />);

    await user.type(screen.getByLabelText("Message"), "Hello{Enter}");

    expect(onSubmit).toHaveBeenCalledOnce();
  });

  it("adds a new line with Shift+Enter", async () => {
    const onSubmit = vi.fn();
    const user = userEvent.setup();

    render(<TestMessageInput onChange={vi.fn()} onSubmit={onSubmit} />);

    await user.type(
      screen.getByLabelText("Message"),
      "Hello{Shift>}{Enter}{/Shift}world",
    );

    expect(onSubmit).not.toHaveBeenCalled();
    expect(screen.getByLabelText("Message")).toHaveValue("Hello\nworld");
  });

  it("exposes the message length limit", () => {
    render(<TestMessageInput onChange={vi.fn()} onSubmit={vi.fn()} />);

    expect(screen.getByLabelText("Message")).toHaveAttribute(
      "maxlength",
      "2000",
    );
    expect(screen.getByText("0 / 2,000")).toBeInTheDocument();
  });
});

type TestMessageInputProps = {
  onChange: (value: string) => void;
  onSubmit: () => void;
};

function TestMessageInput({ onChange, onSubmit }: TestMessageInputProps) {
  const [value, setValue] = useState("");

  function handleChange(nextValue: string) {
    setValue(nextValue);
    onChange(nextValue);
  }

  return (
    <MessageInput onChange={handleChange} onSubmit={onSubmit} value={value} />
  );
}
