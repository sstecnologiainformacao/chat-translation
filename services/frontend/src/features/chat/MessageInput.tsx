import { SendHorizontal } from "lucide-react";
import type { FormEvent, KeyboardEvent } from "react";

import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { MAX_MESSAGE_LENGTH } from "@/types/messages";

type MessageInputProps = {
  onChange: (value: string) => void;
  onSubmit: () => void;
  placeholder?: string;
  value: string;
};

export function MessageInput({
  onChange,
  onSubmit,
  placeholder = "Type a public message",
  value,
}: MessageInputProps) {
  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    onSubmit();
  }

  function handleKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (
      event.key === "Enter" &&
      !event.shiftKey &&
      !event.nativeEvent.isComposing
    ) {
      event.preventDefault();
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
          onChange={(event) => onChange(event.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          rows={1}
          value={value}
        />
        <p className="mt-1 text-right text-xs text-muted-foreground">
          {value.length.toLocaleString()} / {MAX_MESSAGE_LENGTH.toLocaleString()}
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
