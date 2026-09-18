type MessageBubbleProps = {
  author: string;
  conversationLabel?: string | null;
  isOwn?: boolean;
  language: string;
  originalText: string;
  sentAt?: string;
  text: string;
  translationStatus: "completed" | "failed" | "pending";
};

export function MessageBubble({
  author,
  conversationLabel = null,
  isOwn = false,
  language,
  originalText,
  sentAt,
  text,
  translationStatus,
}: MessageBubbleProps) {
  return (
    <article
      className={`max-w-[88%] rounded-lg border px-4 py-3 sm:max-w-[75%] ${
        isOwn
          ? "ml-auto border-primary bg-primary text-primary-foreground"
          : "mr-auto border-border bg-card text-card-foreground"
      }`}
    >
      <div className="mb-2 flex items-start justify-between gap-4">
        <div>
          <p className="text-sm font-medium">{author}</p>
          <p
            className={`text-xs ${isOwn ? "text-primary-foreground/75" : "text-muted-foreground"}`}
          >
            {language}
          </p>
        </div>
        {conversationLabel ? (
          <span className="shrink-0 text-xs opacity-75">
            {conversationLabel}
          </span>
        ) : null}
      </div>
      <p className="whitespace-pre-wrap break-words text-sm leading-6">{text}</p>
      {translationStatus === "pending" ? (
        <div aria-label="Translation pending" className="mt-3 space-y-2">
          <div className="h-3 w-2/3 animate-pulse rounded bg-current opacity-15" />
          <div className="h-3 w-1/3 animate-pulse rounded bg-current opacity-15" />
        </div>
      ) : null}
      {translationStatus === "failed" ? (
        <p className="mt-2 text-sm leading-6 text-destructive">
          Translation unavailable.
        </p>
      ) : null}
      <p
        className={`mt-2 border-t pt-2 text-xs leading-5 ${
          isOwn
            ? "border-primary-foreground/20 text-primary-foreground/75"
            : "border-border text-muted-foreground"
        }`}
      >
        Original: {originalText}
      </p>
      {sentAt ? (
        <time
          className={`mt-1 block text-right text-[11px] ${
            isOwn ? "text-primary-foreground/70" : "text-muted-foreground"
          }`}
          dateTime={sentAt}
        >
          {formatMessageTime(sentAt)}
        </time>
      ) : null}
    </article>
  );
}

function formatMessageTime(sentAt: string): string {
  const date = new Date(sentAt);
  if (Number.isNaN(date.getTime())) {
    return "";
  }

  return new Intl.DateTimeFormat(undefined, {
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}
