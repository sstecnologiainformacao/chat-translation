import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ConnectionBadge } from "@/features/chat/ConnectionBadge";
import { getConnectionLabel } from "@/features/chat/connection";

describe("ConnectionBadge", () => {
  it("shows the unauthenticated connection state", () => {
    render(<ConnectionBadge authenticated={false} status="idle" />);

    expect(screen.getByText("Ready to connect")).toBeInTheDocument();
  });

  it("shows the authenticated connection state", () => {
    render(<ConnectionBadge authenticated status="open" />);

    expect(screen.getByText("Connected")).toBeInTheDocument();
  });

  it("maps WebSocket statuses to readable labels", () => {
    expect(getConnectionLabel("idle")).toBe("Session active");
    expect(getConnectionLabel("connecting")).toBe("Connecting");
    expect(getConnectionLabel("open")).toBe("Connected");
    expect(getConnectionLabel("closed")).toBe("Disconnected");
  });
});
