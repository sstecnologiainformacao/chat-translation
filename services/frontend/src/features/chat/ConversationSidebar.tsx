import { MessageCircle, UserRound } from "lucide-react";

import type { UnreadMessageCounts } from "@/features/chat/useUnreadMessages";
import type { RoomParticipant } from "@/types/messages";

type ConversationSidebarProps = {
  currentNickname: string;
  onSelect: (nickname: string | null) => void;
  selectedNickname: string | null;
  unreadCounts: UnreadMessageCounts;
  users: RoomParticipant[];
};

export function ConversationSidebar({
  currentNickname,
  onSelect,
  selectedNickname,
  unreadCounts,
  users,
}: ConversationSidebarProps) {
  const otherUsers = users.filter((user) => user.nickname !== currentNickname);
  otherUsers.sort((left, right) => {
    const unreadDifference =
      (unreadCounts[right.nickname] ?? 0) - (unreadCounts[left.nickname] ?? 0);

    return unreadDifference || left.nickname.localeCompare(right.nickname);
  });

  return (
    <aside className="shrink-0 border-b border-sidebar-border bg-sidebar px-3 py-3 md:w-60 md:border-r md:border-b-0 md:px-3 md:py-4">
      <p className="mb-2 px-2 text-xs font-medium text-muted-foreground">
        Conversations
      </p>
      <nav
        aria-label="Conversations"
        className="flex gap-1 overflow-x-auto pb-1 md:flex-col md:overflow-visible md:pb-0"
      >
        <button
          type="button"
          aria-label={getConversationAriaLabel(
            "General",
            unreadCounts.general ?? 0,
          )}
          aria-current={selectedNickname === null ? "page" : undefined}
          className="flex min-w-fit items-center justify-between gap-3 rounded-md px-3 py-2 text-left text-sm font-medium transition-colors hover:bg-sidebar-accent/60 aria-[current=page]:bg-primary aria-[current=page]:text-primary-foreground md:w-full"
          onClick={() => onSelect(null)}
        >
          <span className="flex min-w-0 items-center gap-3">
            <MessageCircle className="size-4 shrink-0" aria-hidden="true" />
            <span className="truncate">General</span>
          </span>
          <UnreadBadge count={unreadCounts.general ?? 0} />
        </button>

        {otherUsers.map((user) => (
          <button
            type="button"
            key={user.nickname}
            aria-label={getUserAriaLabel(
              user.nickname,
              user.language,
              unreadCounts[user.nickname] ?? 0,
            )}
            aria-current={
              selectedNickname === user.nickname ? "page" : undefined
            }
            className="group flex min-w-fit items-center gap-3 rounded-md px-3 py-2 text-left transition-colors hover:bg-sidebar-accent/60 aria-[current=page]:bg-primary aria-[current=page]:text-primary-foreground md:w-full"
            onClick={() => onSelect(user.nickname)}
          >
            <span className="relative shrink-0">
              <UserRound className="size-4" aria-hidden="true" />
              <span className="absolute -right-1 -bottom-1 size-2 rounded-full border border-sidebar bg-[#7CB9F3]" />
            </span>
            <span className="min-w-0">
              <span className="block truncate text-sm font-medium">
                {user.nickname}
              </span>
              <span className="block truncate text-xs text-muted-foreground group-aria-[current=page]:text-primary-foreground/75">
                {user.language}
              </span>
            </span>
            <span className="ml-auto">
              <UnreadBadge count={unreadCounts[user.nickname] ?? 0} />
            </span>
          </button>
        ))}
      </nav>

      {otherUsers.length === 0 ? (
        <p className="px-2 pt-3 text-xs leading-5 text-muted-foreground">
          No one else is online.
        </p>
      ) : null}
    </aside>
  );
}

function UnreadBadge({ count }: { count: number }) {
  if (count === 0) {
    return null;
  }

  return (
    <span
      aria-hidden="true"
      className="flex min-w-5 shrink-0 items-center justify-center rounded-full bg-[#046ACC] px-1.5 text-[11px] font-semibold leading-5 text-white"
    >
      {count > 99 ? "99+" : count}
    </span>
  );
}

function getUserAriaLabel(
  nickname: string,
  language: string,
  unreadCount: number,
) {
  return getConversationAriaLabel(`${nickname}, ${language}`, unreadCount);
}

function getConversationAriaLabel(label: string, unreadCount: number) {
  if (unreadCount === 0) {
    return label;
  }

  return `${label}, ${unreadCount} unread ${
    unreadCount === 1 ? "message" : "messages"
  }`;
}
