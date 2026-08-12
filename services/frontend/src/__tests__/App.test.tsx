import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import App from "@/App";
import { useChat } from "@/features/chat/useChat";
import { ApiError, login } from "@/lib/api";
import { clearAuthToken, getAuthSession, saveAuthToken } from "@/lib/auth";

vi.mock("@/lib/api", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api")>("@/lib/api");

  return {
    ...actual,
    login: vi.fn(),
  };
});

vi.mock("@/lib/auth", () => ({
  clearAuthToken: vi.fn(),
  getAuthSession: vi.fn(),
  saveAuthToken: vi.fn(),
}));

vi.mock("@/features/chat/useChat", () => ({
  useChat: vi.fn(),
}));

const mockedLogin = vi.mocked(login);
const mockedClearAuthToken = vi.mocked(clearAuthToken);
const mockedGetAuthSession = vi.mocked(getAuthSession);
const mockedSaveAuthToken = vi.mocked(saveAuthToken);
const mockedUseChat = vi.mocked(useChat);
const sendPublicMessage = vi.fn();

describe("App", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    document.documentElement.classList.remove("dark");
    mockedGetAuthSession.mockReturnValue(null);
    mockedUseChat.mockReturnValue({
      closeReason: null,
      messages: [],
      sendPublicMessage,
      status: "open",
    });
  });

  afterEach(() => {
    document.documentElement.classList.remove("dark");
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

  it("logs in, saves the token, and shows the full-page chat", async () => {
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
      await screen.findByRole("heading", { name: "Public room" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Sign out" }),
    ).toBeInTheDocument();
    expect(mockedUseChat).toHaveBeenLastCalledWith("jwt-token", "Portuguese");
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
    mockedGetAuthSession.mockReturnValue({
      language: "Portuguese",
      nickname: "joao",
      token: "stored-token",
    });
    const user = userEvent.setup();

    render(<App />);

    expect(mockedUseChat).toHaveBeenLastCalledWith(
      "stored-token",
      "Portuguese",
    );
    expect(
      screen.getByRole("heading", { name: "Public room" }),
    ).toBeInTheDocument();
    expect(screen.getByText("joao · Portuguese")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Sign out" }));

    expect(mockedClearAuthToken).toHaveBeenCalled();
    expect(
      screen.getByRole("heading", { name: "Join the room" }),
    ).toBeInTheDocument();
  });

  it("renders received public chat messages", () => {
    mockedGetAuthSession.mockReturnValue({
      language: "Portuguese",
      nickname: "joao",
      token: "stored-token",
    });
    mockedUseChat.mockReturnValue({
      closeReason: null,
      messages: [
        {
          displayText: "Hello",
          id: "msg-1",
          originalText: "Ola",
          senderLanguage: "Portuguese",
          senderNickname: "joao",
          sentAt: "2026-08-11T12:00:00Z",
        },
      ],
      sendPublicMessage,
      status: "open",
    });

    render(<App />);

    expect(screen.getByText("Hello")).toBeInTheDocument();
    expect(screen.getByText("Original: Ola")).toBeInTheDocument();
  });

  it("sends public messages from the composer", async () => {
    mockedGetAuthSession.mockReturnValue({
      language: "Portuguese",
      nickname: "joao",
      token: "stored-token",
    });
    sendPublicMessage.mockReturnValue(true);
    const user = userEvent.setup();

    render(<App />);

    await user.type(screen.getByLabelText("Message"), "Hello public room");
    await user.click(screen.getByRole("button", { name: "Send" }));

    expect(sendPublicMessage).toHaveBeenCalledWith("Hello public room");
    expect(screen.getByLabelText("Message")).toHaveValue("");
  });

  it("toggles dark mode", async () => {
    const user = userEvent.setup();

    render(<App />);

    await user.click(screen.getByRole("button", { name: "Toggle dark mode" }));

    expect(document.documentElement.classList.contains("dark")).toBe(true);

    await user.click(screen.getByRole("button", { name: "Toggle dark mode" }));

    expect(document.documentElement.classList.contains("dark")).toBe(false);
  });
});
