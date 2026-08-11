import type { WebSocketStatus } from "@/lib/useWebSocket";

import { getConnectionLabel } from "./connection";

type ConnectionBadgeProps = {
  authenticated: boolean;
  status: WebSocketStatus;
};

export function ConnectionBadge({
  authenticated,
  status,
}: ConnectionBadgeProps) {
  return (
    <div className="flex items-center gap-2 rounded-full border border-border bg-background px-3 py-1 text-xs text-muted-foreground">
      <span className="size-2 rounded-full bg-primary" />
      {authenticated ? getConnectionLabel(status) : "Ready to connect"}
    </div>
  );
}
