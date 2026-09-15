type MessageBubbleProps = {
  author: string;
  conversationLabel?: string | null;
  language: string;
  originalText: string;
  text: string;
  translationStatus: "completed" | "failed" | "pending";
};

export function MessageBubble({
  author,
  conversationLabel = null,
  language,
  originalText,
  text,
  translationStatus,
}: MessageBubbleProps) {
  return (
    <article className="rounded-lg border border-border p-4">
      <div className="mb-3 flex items-center justify-between gap-3">
        <div>
          <p className="text-sm font-medium">{author}</p>
          <p className="text-xs text-muted-foreground">{language}</p>
        </div>
        {conversationLabel ? (
          <span className="shrink-0 rounded-full border border-border px-2 py-1 text-xs text-muted-foreground">
            {conversationLabel}
          </span>
        ) : null}
      </div>
      <p className="text-base leading-7">{text}</p>
      {translationStatus === "pending" ? (
        <div aria-label="Translation pending" className="mt-3 space-y-2">
          <div className="h-3 w-2/3 animate-pulse rounded bg-muted" />
          <div className="h-3 w-1/3 animate-pulse rounded bg-muted" />
        </div>
      ) : null}
      {translationStatus === "failed" ? (
        <p className="mt-2 text-sm leading-6 text-destructive">
          Translation unavailable.
        </p>
      ) : null}
      <p className="mt-2 text-sm leading-6 text-muted-foreground">
        Original: {originalText}
      </p>
    </article>
  );
}
