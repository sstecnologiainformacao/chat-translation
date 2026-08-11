import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import App from "@/App";

describe("App", () => {
  it("renders the login form and public room preview", () => {
    render(<App />);

    expect(
      screen.getByRole("heading", { name: "Join the room" }),
    ).toBeInTheDocument();
    expect(screen.getByLabelText("Username")).toBeInTheDocument();
    expect(screen.getByLabelText("Password")).toBeInTheDocument();
    expect(screen.getByLabelText("Nickname")).toBeInTheDocument();
    expect(screen.getByLabelText("Language")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /continue/i }),
    ).toBeInTheDocument();
    expect(screen.getByText("Public room")).toBeInTheDocument();
    expect(screen.getByText("Live translation preview")).toBeInTheDocument();
  });
});
