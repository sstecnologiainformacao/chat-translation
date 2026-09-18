import { MessageCircle, UserRound } from "lucide-react";

import type { RoomParticipant } from "@/types/messages";

type ConversationSidebarProps = {
  currentNickname: string;
  onSelect: (nickname: string | null) => void;
  selectedNickname: string | null;
  users: RoomParticipant[];
};

export function ConversationSidebar({
  currentNickname,
  onSelect,
  selectedNickname,
  users,
}: ConversationSidebarProps) {
  const otherUsers = users.filter(
    (user) => user.nickname !== currentNickname,
  );

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
          aria-current={selectedNickname === null ? "page" : undefined}
          className="flex min-w-fit items-center gap-3 rounded-md px-3 py-2 text-left text-sm font-medium transition-colors hover:bg-sidebar-accent/60 aria-[current=page]:bg-primary aria-[current=page]:text-primary-foreground md:w-full"
          onClick={() => onSelect(null)}
        >
          <MessageCircle className="size-4" aria-hidden="true" />
          <span className="min-w-0 truncate">General</span>
        </button>

        {otherUsers.map((user) => (
          <button
            type="button"
            key={user.nickname}
            aria-label={`${user.nickname}, ${user.language}`}
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
