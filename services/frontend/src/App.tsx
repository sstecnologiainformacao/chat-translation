import type { FormEvent } from "react";
import { useEffect, useState } from "react";
import {
  ArrowRight,
  Languages,
  Lock,
  MessageCircle,
  Moon,
  Sun,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ConnectionBadge } from "@/features/chat/ConnectionBadge";
import { MessageBubble } from "@/features/chat/MessageBubble";
import { MessageInput } from "@/features/chat/MessageInput";
import { MessageList } from "@/features/chat/MessageList";
import { useChat } from "@/features/chat/useChat";
import { ApiError, login, register } from "@/lib/api";
import { clearAuthToken, getAuthSession, saveAuthToken } from "@/lib/auth";
import { SUPPORTED_LANGUAGES } from "@/lib/languages";
import {
  applyTheme,
  getNextTheme,
  getStoredTheme,
  saveTheme,
} from "@/lib/theme";
import type { LoginRequest } from "@/types/auth";

type AuthMode = "login" | "register";

const sampleMessages = [
  {
    author: "Joao",
    language: "Portuguese",
    translated: "How are you today?",
    original: "Como voce esta hoje?",
  },
  {
    author: "Maria",
    language: "English",
    translated: "Estou bem, obrigado.",
    original: "I am good, thanks.",
  },
];

function App() {
  const [authSession, setAuthSession] = useState(() => getAuthSession());
  const [authMode, setAuthMode] = useState<AuthMode>("login");
  const [composerText, setComposerText] = useState("");
  const [loginError, setLoginError] = useState<string | null>(null);
  const [registerError, setRegisterError] = useState<string | null>(null);
  const [registerSuccess, setRegisterSuccess] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [theme, setTheme] = useState(() => getStoredTheme());
  const authToken = authSession?.token ?? null;
  const chat = useChat(authToken, authSession?.language ?? null);

  useEffect(() => {
    applyTheme(theme);
    saveTheme(theme);
  }, [theme]);

  async function handleLogin(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoginError(null);
    setSubmitting(true);

    const formData = new FormData(event.currentTarget);
    const payload: LoginRequest = {
      username: String(formData.get("username") ?? ""),
      password: String(formData.get("password") ?? ""),
    };

    try {
      const response = await login(payload);
      saveAuthToken(response.token);
      const nextSession = getAuthSession();

      if (nextSession === null) {
        setLoginError("Sign in failed.");
        return;
      }

      setAuthSession(nextSession);
    } catch (error) {
      setLoginError(getLoginErrorMessage(error));
    } finally {
      setSubmitting(false);
    }
  }

  async function handleRegister(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setRegisterError(null);
    setRegisterSuccess(null);
    setSubmitting(true);

    const formData = new FormData(event.currentTarget);
    const username = String(formData.get("username") ?? "");

    try {
      const response = await register({
        username,
        password: String(formData.get("password") ?? ""),
        nickname: String(formData.get("nickname") ?? ""),
        language: String(formData.get("language") ?? ""),
      });
      setRegisterSuccess(`${response.username} was created. Sign in now.`);
      setAuthMode("login");
    } catch (error) {
      setRegisterError(getRegisterErrorMessage(error));
    } finally {
      setSubmitting(false);
    }
  }

  function handleSignOut() {
    clearAuthToken();
    setAuthSession(null);
    setComposerText("");
    setLoginError(null);
  }

  function handleSendMessage() {
    if (chat.sendPublicMessage(composerText)) {
      setComposerText("");
    }
  }

  function handleToggleTheme() {
    setTheme((currentTheme) => getNextTheme(currentTheme));
  }

  if (authSession !== null) {
    return (
      <main className="flex h-dvh flex-col overflow-hidden bg-background text-foreground">
        <header className="shrink-0 border-b border-border bg-background/95 px-4 py-3 backdrop-blur sm:px-6">
          <div className="mx-auto flex w-full max-w-5xl items-center justify-between gap-3">
            <div className="flex min-w-0 items-center gap-3">
              <span className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-primary text-primary-foreground">
                <MessageCircle className="size-4" aria-hidden="true" />
              </span>
              <div className="min-w-0">
                <h1 className="truncate text-base font-semibold">
                  Public room
                </h1>
                <p className="truncate text-xs text-muted-foreground">
                  {authSession.nickname} · {authSession.language}
                </p>
              </div>
            </div>

            <div className="flex shrink-0 items-center gap-2">
              <ConnectionBadge authenticated status={chat.status} />
              <Button
                type="button"
                variant="outline"
                size="icon"
                onClick={handleToggleTheme}
                aria-label="Toggle dark mode"
              >
                {theme === "dark" ? (
                  <Sun className="size-4" aria-hidden="true" />
                ) : (
                  <Moon className="size-4" aria-hidden="true" />
                )}
              </Button>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={handleSignOut}
              >
                Sign out
              </Button>
            </div>
          </div>
        </header>

        <section className="flex min-h-0 flex-1 overflow-y-auto px-4 sm:px-6">
          <div className="mx-auto flex w-full max-w-3xl flex-col gap-3 py-4">
            <MessageList messages={chat.messages} />
          </div>
        </section>

        <footer className="shrink-0 border-t border-border bg-background/95 px-4 py-3 backdrop-blur sm:px-6">
          <div className="mx-auto w-full max-w-3xl">
            <MessageInput
              onChange={setComposerText}
              onSubmit={handleSendMessage}
              value={composerText}
            />
          </div>
        </footer>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-background text-foreground">
      <section className="mx-auto grid min-h-screen w-full max-w-6xl grid-cols-1 lg:grid-cols-[0.92fr_1.08fr]">
        <div className="flex min-h-[48rem] flex-col justify-between border-border px-5 py-6 sm:px-8 lg:border-r lg:px-10">
          <header className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-sm font-medium">
              <span className="flex size-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
                <Languages className="size-4" aria-hidden="true" />
              </span>
              Chat Translation
            </div>
            <div className="flex items-center gap-2">
              <Button
                type="button"
                variant="outline"
                size="icon"
                onClick={handleToggleTheme}
                aria-label="Toggle dark mode"
              >
                {theme === "dark" ? (
                  <Sun className="size-4" aria-hidden="true" />
                ) : (
                  <Moon className="size-4" aria-hidden="true" />
                )}
              </Button>
              <span className="rounded-full border border-border px-3 py-1 text-xs text-muted-foreground">
                Local MVP
              </span>
            </div>
          </header>

          <div className="mx-auto flex w-full max-w-sm flex-1 flex-col justify-center py-12">
            <div className="mb-8 space-y-3">
              <div className="flex size-10 items-center justify-center rounded-lg bg-muted text-muted-foreground">
                <Lock className="size-5" aria-hidden="true" />
              </div>
              <div>
                <h1 className="text-3xl font-semibold tracking-tight">
                  {authMode === "login" ? "Join the room" : "Create account"}
                </h1>
                <p className="mt-2 text-sm leading-6 text-muted-foreground">
                  {authMode === "login"
                    ? "Sign in with your local account."
                    : "Create a local user with your @deploy.co email, profile, and password."}
                </p>
              </div>
            </div>

            {authMode === "login" ? (
              <form
                className="space-y-5"
                aria-label="Login form"
                onSubmit={handleLogin}
              >
                <div className="space-y-2">
                  <Label htmlFor="username">Deploy email</Label>
                  <Input
                    id="username"
                    name="username"
                    autoComplete="email"
                    inputMode="email"
                    placeholder="name@deploy.co"
                    required
                    type="email"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="password">Password</Label>
                  <Input
                    id="password"
                    name="password"
                    type="password"
                    autoComplete="current-password"
                    required
                  />
                </div>

                {registerSuccess ? (
                  <p className="rounded-lg border border-primary/30 bg-primary/10 px-3 py-2 text-sm text-primary">
                    {registerSuccess}
                  </p>
                ) : null}

                {loginError ? (
                  <p className="rounded-lg border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive">
                    {loginError}
                  </p>
                ) : null}

                <Button
                  type="submit"
                  className="h-10 w-full"
                  disabled={submitting}
                >
                  {submitting ? "Signing in" : "Continue"}
                  <ArrowRight className="size-4" aria-hidden="true" />
                </Button>
              </form>
            ) : (
              <form
                className="space-y-5"
                aria-label="Create account form"
                onSubmit={handleRegister}
              >
                <div className="space-y-2">
                  <Label htmlFor="register-username">Deploy email</Label>
                  <Input
                    id="register-username"
                    name="username"
                    autoComplete="email"
                    inputMode="email"
                    placeholder="name@deploy.co"
                    required
                    type="email"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="register-password">Password</Label>
                  <Input
                    id="register-password"
                    name="password"
                    type="password"
                    autoComplete="new-password"
                    minLength={8}
                    required
                  />
                </div>

                <div className="grid gap-5 sm:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="register-nickname">Nickname</Label>
                    <Input
                      id="register-nickname"
                      name="nickname"
                      autoComplete="nickname"
                      required
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="register-language">Language</Label>
                    <select
                      className="h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm text-foreground shadow-xs outline-none transition-[color,box-shadow] focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-ring/50 disabled:pointer-events-none disabled:cursor-not-allowed disabled:opacity-50"
                      id="register-language"
                      name="language"
                      defaultValue=""
                      required
                    >
                      <option value="" disabled>
                        Select language
                      </option>
                      {SUPPORTED_LANGUAGES.map((language) => (
                        <option key={language} value={language}>
                          {language}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                {registerError ? (
                  <p className="rounded-lg border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive">
                    {registerError}
                  </p>
                ) : null}

                <Button
                  type="submit"
                  className="h-10 w-full"
                  disabled={submitting}
                >
                  {submitting ? "Creating account" : "Create account"}
                  <ArrowRight className="size-4" aria-hidden="true" />
                </Button>
              </form>
            )}

            <Button
              type="button"
              variant="outline"
              className="mt-4 h-10 w-full"
              onClick={() => {
                setAuthMode(authMode === "login" ? "register" : "login");
                setLoginError(null);
                setRegisterError(null);
              }}
            >
              {authMode === "login" ? "Create a new account" : "Back to sign in"}
            </Button>
          </div>

          <p className="text-xs leading-5 text-muted-foreground">
            The browser stores the session token locally for the MVP. The server
            remains the source of truth for token validation.
          </p>
        </div>

        <div className="flex min-h-[42rem] items-center bg-muted/40 px-5 py-8 sm:px-8 lg:px-10">
          <div className="mx-auto w-full max-w-xl">
            <div className="mb-5 flex items-center justify-between">
              <div>
                <p className="text-sm font-medium">Public room</p>
                <p className="text-xs text-muted-foreground">general</p>
              </div>
              <ConnectionBadge authenticated={false} status="idle" />
            </div>

            <div className="overflow-hidden rounded-xl border border-border bg-background shadow-sm">
              <div className="flex items-center gap-2 border-b border-border px-4 py-3">
                <MessageCircle
                  className="size-4 text-muted-foreground"
                  aria-hidden="true"
                />
                <span className="text-sm font-medium">
                  Live translation preview
                </span>
              </div>

              <div className="space-y-4 p-4">
                {sampleMessages.map((message) => (
                  <MessageBubble
                    key={message.original}
                    author={message.author}
                    language={message.language}
                    originalText={message.original}
                    text={message.translated}
                    translationStatus="completed"
                  />
                ))}
              </div>

              <div className="border-t border-border p-4">
                <div className="flex min-h-11 items-center rounded-lg border border-input bg-muted/60 px-3 text-sm text-muted-foreground">
                  Message composer will appear after login.
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}

function getLoginErrorMessage(error: unknown): string {
  if (error instanceof ApiError && error.detail === "invalid_credentials") {
    return "Invalid username or password.";
  }

  if (error instanceof ApiError && error.detail === "network_error") {
    return "Could not connect to the server.";
  }

  return "Sign in failed.";
}

function getRegisterErrorMessage(error: unknown): string {
  if (error instanceof ApiError && error.detail === "user_already_exists") {
    return "This user already exists.";
  }

  if (error instanceof ApiError && error.detail === "network_error") {
    return "Could not connect to the server.";
  }

  return "Use a valid @deploy.co email and password.";
}

export default App;
