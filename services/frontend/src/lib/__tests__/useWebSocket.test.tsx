import { act, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { useWebSocket } from "@/lib/useWebSocket";

describe("useWebSocket", () => {
  beforeEach(() => {
    MockWebSocket.instances = [];
    vi.stubGlobal("WebSocket", MockWebSocket);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("stays idle when no URL is provided", () => {
    const { result } = renderHook(() => useWebSocket(null));

    expect(result.current.status).toBe("idle");
    expect(result.current.messages).toEqual([]);
    expect(result.current.closeReason).toBeNull();
  });

  it("opens a socket and stores received JSON messages", () => {
    const { result } = renderHook(() =>
      useWebSocket<{ type: string }>("ws://localhost/ws"),
    );
    const socket = MockWebSocket.instances[0];

    expect(socket.url).toBe("ws://localhost/ws");
    expect(result.current.status).toBe("connecting");

    act(() => {
      socket.open();
    });

    expect(result.current.status).toBe("open");

    act(() => {
      socket.receive({ type: "room_message" });
    });

    expect(result.current.messages).toEqual([{ type: "room_message" }]);
  });

  it("sends JSON only when the socket is open", () => {
    const { result } = renderHook(() => useWebSocket("ws://localhost/ws"));
    const socket = MockWebSocket.instances[0];

    expect(result.current.sendJson({ type: "room_message" })).toBe(false);

    act(() => {
      socket.open();
    });

    expect(result.current.sendJson({ type: "room_message" })).toBe(true);
    expect(socket.send).toHaveBeenCalledWith(
      JSON.stringify({ type: "room_message" }),
    );
  });

  it("tracks close reason", () => {
    const { result } = renderHook(() => useWebSocket("ws://localhost/ws"));
    const socket = MockWebSocket.instances[0];

    act(() => {
      socket.closeWithReason("invalid_session");
    });

    expect(result.current.status).toBe("closed");
    expect(result.current.closeReason).toBe("invalid_session");
  });
});

class MockWebSocket {
  static readonly OPEN = 1;
  static readonly CLOSED = 3;
  static instances: MockWebSocket[] = [];

  onclose: ((event: CloseEvent) => void) | null = null;
  onmessage: ((event: MessageEvent) => void) | null = null;
  onopen: (() => void) | null = null;
  readyState = 0;
  readonly send = vi.fn();
  readonly url: string;

  constructor(url: string) {
    this.url = url;
    MockWebSocket.instances.push(this);
  }

  close() {
    this.readyState = MockWebSocket.CLOSED;
  }

  closeWithReason(reason: string) {
    this.readyState = MockWebSocket.CLOSED;
    this.onclose?.({ reason } as CloseEvent);
  }

  open() {
    this.readyState = MockWebSocket.OPEN;
    this.onopen?.();
  }

  receive(payload: unknown) {
    this.onmessage?.({ data: JSON.stringify(payload) } as MessageEvent);
  }
}
