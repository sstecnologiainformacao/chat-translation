import { ArrowDown } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import type { UIEvent } from "react";

import { Button } from "@/components/ui/button";
import type { ChatMessage } from "@/features/chat/useChat";

import { MessageBubble } from "./MessageBubble";

type MessageListProps = {
  conversationKey: string;
  currentNickname: string;
  messages: ChatMessage[];
};

const NEAR_BOTTOM_THRESHOLD_PX = 80;

type MessageListViewState = {
  conversationKey: string;
  isNearBottom: boolean;
  lastMessageId: string | null;
  messageCount: number;
  newMessageCount: number;
  scrollBehavior: ScrollBehavior | null;
};

export function MessageList({
  conversationKey,
  currentNickname,
  messages,
}: MessageListProps) {
  const viewportRef = useRef<HTMLDivElement>(null);
  const lastMessageId = messages.at(-1)?.id ?? null;
  const [viewState, setViewState] = useState<MessageListViewState>(() => ({
    conversationKey,
    isNearBottom: true,
    lastMessageId,
    messageCount: messages.length,
    newMessageCount: 0,
    scrollBehavior: lastMessageId === null ? null : "auto",
  }));

  const scrollToLatest = useCallback((behavior: ScrollBehavior) => {
    const viewport = viewportRef.current;
    if (viewport === null) {
      return;
    }

    if (typeof viewport.scrollTo === "function") {
      viewport.scrollTo({ behavior, top: viewport.scrollHeight });
      return;
    }

    viewport.scrollTop = viewport.scrollHeight;
  }, []);

  if (
    viewState.conversationKey !== conversationKey ||
    viewState.lastMessageId !== lastMessageId
  ) {
    const conversationChanged = viewState.conversationKey !== conversationKey;
    const addedMessages = Math.max(messages.length - viewState.messageCount, 1);
    const shouldFollowLatest = conversationChanged || viewState.isNearBottom;

    setViewState({
      conversationKey,
      isNearBottom: shouldFollowLatest,
      lastMessageId,
      messageCount: messages.length,
      newMessageCount:
        shouldFollowLatest || lastMessageId === null
          ? 0
          : viewState.newMessageCount + addedMessages,
      scrollBehavior:
        lastMessageId === null
          ? null
          : conversationChanged
            ? "auto"
            : shouldFollowLatest
              ? "smooth"
              : null,
    });
  }

  useEffect(() => {
    if (viewState.scrollBehavior !== null) {
      scrollToLatest(viewState.scrollBehavior);
    }
  }, [
    scrollToLatest,
    viewState.conversationKey,
    viewState.lastMessageId,
    viewState.scrollBehavior,
  ]);

  function handleScroll(event: UIEvent<HTMLDivElement>) {
    const viewport = event.currentTarget;
    const distanceFromBottom =
      viewport.scrollHeight - viewport.scrollTop - viewport.clientHeight;
    const isNearBottom = distanceFromBottom <= NEAR_BOTTOM_THRESHOLD_PX;

    setViewState((currentState) => {
      const newMessageCount = isNearBottom ? 0 : currentState.newMessageCount;

      if (
        currentState.isNearBottom === isNearBottom &&
        currentState.newMessageCount === newMessageCount
      ) {
        return currentState;
      }

      return {
        ...currentState,
        isNearBottom,
        newMessageCount,
      };
    });
  }

  function handleShowLatest() {
    scrollToLatest("smooth");
    setViewState((currentState) => ({
      ...currentState,
      isNearBottom: true,
      newMessageCount: 0,
    }));
  }

  return (
    <div className="relative min-h-0 flex-1">
      <div
        aria-label="Messages"
        aria-live="polite"
        className="h-full overflow-y-auto px-4 sm:px-6"
        onScroll={handleScroll}
        ref={viewportRef}
        role="log"
      >
        <div className="mx-auto flex min-h-full w-full max-w-3xl flex-col gap-3 py-5">
          {messages.length === 0 ? (
            <div className="flex flex-1 items-center justify-center px-6 py-16 text-center text-sm text-muted-foreground">
              Start the conversation.
            </div>
          ) : (
            messages.map((message) => (
              <MessageBubble
                key={message.id}
                author={message.senderNickname}
                conversationLabel={
                  message.conversationKind === "private"
                    ? `Private to ${message.recipientNickname}`
                    : null
                }
                language={message.senderLanguage}
                isOwn={message.senderNickname === currentNickname}
                originalText={message.originalText}
                sentAt={message.sentAt}
                text={message.displayText}
                translationStatus={message.translationStatus}
              />
            ))
          )}
        </div>
      </div>

      {viewState.newMessageCount > 0 ? (
        <Button
          className="absolute bottom-4 left-1/2 z-10 -translate-x-1/2 shadow-lg"
          onClick={handleShowLatest}
          size="sm"
          type="button"
        >
          <ArrowDown aria-hidden="true" data-icon="inline-start" />
          {viewState.newMessageCount} new{" "}
          {viewState.newMessageCount === 1 ? "message" : "messages"}
        </Button>
      ) : null}
    </div>
  );
}
