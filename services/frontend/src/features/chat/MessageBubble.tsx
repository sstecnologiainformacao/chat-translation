type MessageBubbleProps = {
  author: string;
  language: string;
  originalText: string;
  text: string;
};

export function MessageBubble({
  author,
  language,
  originalText,
  text,
}: MessageBubbleProps) {
  return (
    <article className="rounded-lg border border-border p-4">
      <div className="mb-3 flex items-center justify-between gap-3">
        <div>
          <p className="text-sm font-medium">{author}</p>
          <p className="text-xs text-muted-foreground">{language}</p>
        </div>
      </div>
      <p className="text-base leading-7">{text}</p>
      <p className="mt-2 text-sm leading-6 text-muted-foreground">
        Original: {originalText}
      </p>
    </article>
  );
}
