import type { WebSocketStatus } from "@/lib/useWebSocket";

export function getConnectionLabel(status: WebSocketStatus): string {
  if (status === "open") {
    return "Connected";
  }

  if (status === "connecting") {
    return "Connecting";
  }

  if (status === "closed") {
    return "Disconnected";
  }

  return "Session active";
}
