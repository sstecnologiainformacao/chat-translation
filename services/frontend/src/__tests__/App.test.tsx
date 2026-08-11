import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import App from "@/App";
import { ApiError, login } from "@/lib/api";
import { clearAuthToken, hasAuthToken, saveAuthToken } from "@/lib/auth";

vi.mock("@/lib/api", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api")>("@/lib/api");

  return {
    ...actual,
    login: vi.fn(),
  };
});

vi.mock("@/lib/auth", () => ({
  clearAuthToken: vi.fn(),
  hasAuthToken: vi.fn(),
  saveAuthToken: vi.fn(),
}));

const mockedLogin = vi.mocked(login);
const mockedClearAuthToken = vi.mocked(clearAuthToken);
const mockedHasAuthToken = vi.mocked(hasAuthToken);
const mockedSaveAuthToken = vi.mocked(saveAuthToken);

describe("App", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockedHasAuthToken.mockReturnValue(false);
  });

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

  it("logs in, saves the token, and shows the connected state", async () => {
    mockedLogin.mockResolvedValue({ token: "jwt-token" });
    const user = userEvent.setup();

    render(<App />);

    await user.type(screen.getByLabelText("Username"), "local-user");
    await user.type(screen.getByLabelText("Password"), "local-pass");
    await user.type(screen.getByLabelText("Nickname"), "joao");
    await user.type(screen.getByLabelText("Language"), "Portuguese");
    await user.click(screen.getByRole("button", { name: /continue/i }));

    expect(mockedLogin).toHaveBeenCalledWith({
      username: "local-user",
      password: "local-pass",
      nickname: "joao",
      language: "Portuguese",
    });
    expect(mockedSaveAuthToken).toHaveBeenCalledWith("jwt-token");
    expect(
      await screen.findByRole("heading", { name: "Connected" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Sign out" }),
    ).toBeInTheDocument();
  });

  it("shows a readable message when credentials are invalid", async () => {
    mockedLogin.mockRejectedValue(
      new ApiError({ status: 401, detail: "invalid_credentials" }),
    );
    const user = userEvent.setup();

    render(<App />);

    await user.type(screen.getByLabelText("Username"), "wrong-user");
    await user.type(screen.getByLabelText("Password"), "wrong-pass");
    await user.type(screen.getByLabelText("Nickname"), "joao");
    await user.type(screen.getByLabelText("Language"), "Portuguese");
    await user.click(screen.getByRole("button", { name: /continue/i }));

    expect(
      await screen.findByText("Invalid username or password."),
    ).toBeInTheDocument();
    expect(mockedSaveAuthToken).not.toHaveBeenCalled();
  });

  it("starts connected when a token already exists and can sign out", async () => {
    mockedHasAuthToken.mockReturnValue(true);
    const user = userEvent.setup();

    render(<App />);

    expect(
      screen.getByRole("heading", { name: "Connected" }),
    ).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Sign out" }));

    expect(mockedClearAuthToken).toHaveBeenCalled();
    expect(
      screen.getByRole("heading", { name: "Join the room" }),
    ).toBeInTheDocument();
  });
});
