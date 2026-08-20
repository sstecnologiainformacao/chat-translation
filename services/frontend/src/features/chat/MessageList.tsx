import type { ChatMessage } from "@/features/chat/useChat";

import { MessageBubble } from "./MessageBubble";

type MessageListProps = {
  messages: ChatMessage[];
};

export function MessageList({ messages }: MessageListProps) {
  if (messages.length === 0) {
    return (
      <div className="rounded-lg border border-dashed border-border p-6 text-center text-sm text-muted-foreground">
        No messages yet.
      </div>
    );
  }

  return messages.map((message) => (
    <MessageBubble
      key={message.id}
      author={message.senderNickname}
      language={message.senderLanguage}
      originalText={message.originalText}
      text={message.displayText}
      translationStatus={message.translationStatus}
    />
  ));
}
