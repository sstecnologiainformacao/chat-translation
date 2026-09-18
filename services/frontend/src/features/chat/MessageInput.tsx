import { SendHorizontal } from "lucide-react";
import { useCallback, useEffect, useRef } from "react";
import type { ChangeEvent, FormEvent, KeyboardEvent } from "react";

import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { MAX_MESSAGE_LENGTH } from "@/types/messages";

type MessageInputProps = {
  onChange: (value: string) => void;
  onSubmit: () => void;
  onTypingChange?: (isTyping: boolean) => void;
  placeholder?: string;
  value: string;
};

const TYPING_HEARTBEAT_MS = 1000;
const TYPING_IDLE_TIMEOUT_MS = 1500;

export function MessageInput({
  onChange,
  onSubmit,
  onTypingChange,
  placeholder = "Type a public message",
  value,
}: MessageInputProps) {
  const isTypingRef = useRef(false);
  const lastTypingEventAtRef = useRef(0);
  const typingTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const stopTyping = useCallback(() => {
    if (typingTimeoutRef.current !== null) {
      clearTimeout(typingTimeoutRef.current);
      typingTimeoutRef.current = null;
    }

    if (isTypingRef.current) {
      isTypingRef.current = false;
      lastTypingEventAtRef.current = 0;
      onTypingChange?.(false);
    }
  }, [onTypingChange]);

  useEffect(() => stopTyping, [stopTyping]);

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    stopTyping();
    onSubmit();
  }

  function handleChange(event: ChangeEvent<HTMLTextAreaElement>) {
    const nextValue = event.target.value;
    onChange(nextValue);

    if (!nextValue.trim()) {
      stopTyping();
      return;
    }

    const now = Date.now();
    if (
      !isTypingRef.current ||
      now - lastTypingEventAtRef.current >= TYPING_HEARTBEAT_MS
    ) {
      isTypingRef.current = true;
      lastTypingEventAtRef.current = now;
      onTypingChange?.(true);
    }

    if (typingTimeoutRef.current !== null) {
      clearTimeout(typingTimeoutRef.current);
    }
    typingTimeoutRef.current = setTimeout(stopTyping, TYPING_IDLE_TIMEOUT_MS);
  }

  function handleKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (
      event.key === "Enter" &&
      !event.shiftKey &&
      !event.nativeEvent.isComposing
    ) {
      event.preventDefault();
      stopTyping();
      onSubmit();
    }
  }

  return (
    <form className="flex items-end gap-2" onSubmit={handleSubmit}>
      <div className="min-w-0 flex-1">
        <Textarea
          aria-label="Message"
          className="max-h-32 min-h-11 resize-none bg-background"
          maxLength={MAX_MESSAGE_LENGTH}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          rows={1}
          value={value}
        />
        <p className="mt-1 text-right text-xs text-muted-foreground">
          {value.length.toLocaleString()} /{" "}
          {MAX_MESSAGE_LENGTH.toLocaleString()}
        </p>
      </div>
      <Button
        type="submit"
        size="icon-lg"
        aria-label="Send message"
        disabled={!value.trim()}
        title="Send message"
      >
        <SendHorizontal className="size-4" aria-hidden="true" />
      </Button>
    </form>
  );
}
