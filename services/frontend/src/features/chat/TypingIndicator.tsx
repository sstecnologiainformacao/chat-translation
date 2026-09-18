type TypingIndicatorProps = {
  nicknames: string[];
};

export function TypingIndicator({ nicknames }: TypingIndicatorProps) {
  const message = getTypingMessage(nicknames);

  return (
    <div className="flex min-h-5 items-center gap-2 text-xs text-muted-foreground">
      {message ? (
        <>
          <span aria-hidden="true" className="flex items-center gap-0.5">
            <span className="size-1 animate-pulse rounded-full bg-current" />
            <span className="size-1 animate-pulse rounded-full bg-current [animation-delay:150ms]" />
            <span className="size-1 animate-pulse rounded-full bg-current [animation-delay:300ms]" />
          </span>
          <span aria-live="polite" role="status">
            {message}
          </span>
        </>
      ) : null}
    </div>
  );
}

function getTypingMessage(nicknames: string[]): string | null {
  if (nicknames.length === 0) {
    return null;
  }

  if (nicknames.length === 1) {
    return `${nicknames[0]} is typing...`;
  }

  if (nicknames.length === 2) {
    return `${nicknames[0]} and ${nicknames[1]} are typing...`;
  }

  return `${nicknames[0]} and ${nicknames.length - 1} others are typing...`;
}
