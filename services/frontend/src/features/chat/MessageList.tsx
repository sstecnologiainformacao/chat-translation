import { useEffect, useRef } from "react";

import type { ChatMessage } from "@/features/chat/useChat";

import { MessageBubble } from "./MessageBubble";

type MessageListProps = {
  currentNickname: string;
  messages: ChatMessage[];
};

export function MessageList({ currentNickname, messages }: MessageListProps) {
  const endOfMessagesRef = useRef<HTMLDivElement>(null);
  const lastMessageId = messages.at(-1)?.id ?? null;

  useEffect(() => {
    if (lastMessageId === null) {
      return;
    }

    endOfMessagesRef.current?.scrollIntoView?.({
      behavior: "smooth",
      block: "end",
    });
  }, [lastMessageId]);

  return (
    <>
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
      <div ref={endOfMessagesRef} aria-hidden="true" />
    </>
  );
}
