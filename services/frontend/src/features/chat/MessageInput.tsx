import type { FormEvent } from "react";

import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";

type MessageInputProps = {
  onChange: (value: string) => void;
  onSubmit: () => void;
  value: string;
};

export function MessageInput({ onChange, onSubmit, value }: MessageInputProps) {
  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    onSubmit();
  }

  return (
    <form className="flex gap-2" onSubmit={handleSubmit}>
      <Textarea
        aria-label="Message"
        className="min-h-11 resize-none"
        onChange={(event) => onChange(event.target.value)}
        placeholder="Type a public message"
        value={value}
      />
      <Button type="submit" className="h-11">
        Send
      </Button>
    </form>
  );
}
