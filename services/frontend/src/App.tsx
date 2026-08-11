import { ArrowRight, Languages, Lock, MessageCircle } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

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
            <span className="rounded-full border border-border px-3 py-1 text-xs text-muted-foreground">
              Local MVP
            </span>
          </header>

          <div className="mx-auto flex w-full max-w-sm flex-1 flex-col justify-center py-12">
            <div className="mb-8 space-y-3">
              <div className="flex size-10 items-center justify-center rounded-lg bg-muted text-muted-foreground">
                <Lock className="size-5" aria-hidden="true" />
              </div>
              <div>
                <h1 className="text-3xl font-semibold tracking-tight">
                  Join the room
                </h1>
                <p className="mt-2 text-sm leading-6 text-muted-foreground">
                  Sign in with the local shared credentials, choose a nickname,
                  and type your preferred language.
                </p>
              </div>
            </div>

            <form className="space-y-5" aria-label="Login form">
              <div className="space-y-2">
                <Label htmlFor="username">Username</Label>
                <Input id="username" name="username" autoComplete="username" />
              </div>

              <div className="space-y-2">
                <Label htmlFor="password">Password</Label>
                <Input
                  id="password"
                  name="password"
                  type="password"
                  autoComplete="current-password"
                />
              </div>

              <div className="grid gap-5 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="nickname">Nickname</Label>
                  <Input
                    id="nickname"
                    name="nickname"
                    autoComplete="nickname"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="language">Language</Label>
                  <Input
                    id="language"
                    name="language"
                    placeholder="Portuguese"
                  />
                </div>
              </div>

              <Button type="submit" className="h-10 w-full">
                Continue
                <ArrowRight className="size-4" aria-hidden="true" />
              </Button>
            </form>
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
              <div className="flex items-center gap-2 rounded-full border border-border bg-background px-3 py-1 text-xs text-muted-foreground">
                <span className="size-2 rounded-full bg-primary" />
                Ready to connect
              </div>
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
                  <article
                    key={message.original}
                    className="rounded-lg border border-border p-4"
                  >
                    <div className="mb-3 flex items-center justify-between gap-3">
                      <div>
                        <p className="text-sm font-medium">{message.author}</p>
                        <p className="text-xs text-muted-foreground">
                          {message.language}
                        </p>
                      </div>
                    </div>
                    <p className="text-base leading-7">{message.translated}</p>
                    <p className="mt-2 text-sm leading-6 text-muted-foreground">
                      Original: {message.original}
                    </p>
                  </article>
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

export default App;
