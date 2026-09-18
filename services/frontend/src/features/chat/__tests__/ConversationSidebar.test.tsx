import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { ConversationSidebar } from "@/features/chat/ConversationSidebar";

const users = [
  { language: "Portuguese", nickname: "joao" },
  { language: "Spanish", nickname: "ana" },
  { language: "English", nickname: "maria" },
];

describe("ConversationSidebar", () => {
  it("shows unread counts with accessible conversation labels", () => {
    render(
      <ConversationSidebar
        currentNickname="joao"
        onSelect={vi.fn()}
        selectedNickname={null}
        unreadCounts={{ general: 3, maria: 1 }}
        users={users}
      />,
    );

    expect(
      screen.getByRole("button", {
        name: "General, 3 unread messages",
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", {
        name: "maria, English, 1 unread message",
      }),
    ).toBeInTheDocument();
    expect(
      screen.getAllByRole("button").map((button) => button.textContent),
    ).toEqual(["General3", "mariaEnglish1", "anaSpanish"]);
  });

  it("caps the visual badge without changing the accessible count", () => {
    render(
      <ConversationSidebar
        currentNickname="joao"
        onSelect={vi.fn()}
        selectedNickname={null}
        unreadCounts={{ maria: 120 }}
        users={users}
      />,
    );

    expect(screen.getByText("99+")).toBeInTheDocument();
    expect(
      screen.getByRole("button", {
        name: "maria, English, 120 unread messages",
      }),
    ).toBeInTheDocument();
  });

  it("selects public and private conversations", async () => {
    const onSelect = vi.fn();
    const user = userEvent.setup();
    render(
      <ConversationSidebar
        currentNickname="joao"
        onSelect={onSelect}
        selectedNickname="maria"
        unreadCounts={{}}
        users={users}
      />,
    );

    await user.click(screen.getByRole("button", { name: "General" }));
    await user.click(screen.getByRole("button", { name: "maria, English" }));

    expect(onSelect).toHaveBeenNthCalledWith(1, null);
    expect(onSelect).toHaveBeenNthCalledWith(2, "maria");
  });
});
