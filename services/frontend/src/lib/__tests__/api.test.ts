import { afterEach, describe, expect, it, vi } from "vitest";

import { buildApiUrl, getApiBaseUrl, login } from "@/lib/api";
import type { LoginRequest } from "@/types/auth";

const loginPayload: LoginRequest = {
  username: "local-user",
  password: "local-pass",
  nickname: "joao",
  language: "Portuguese",
};

describe("api helpers", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("uses the default API URL when no value is configured", () => {
    expect(getApiBaseUrl(undefined)).toBe("http://localhost:8000");
  });

  it("removes trailing slashes from the configured API URL", () => {
    expect(getApiBaseUrl("http://127.0.0.1:8000///")).toBe(
      "http://127.0.0.1:8000",
    );
  });

  it("builds API URLs with a leading slash", () => {
    expect(buildApiUrl("auth/login", "http://127.0.0.1:8000")).toBe(
      "http://127.0.0.1:8000/auth/login",
    );
  });

  it("sends login credentials and returns the token", async () => {
    const fetcher = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ token: "jwt-token" }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );

    await expect(
      login(loginPayload, {
        apiBaseUrl: "http://127.0.0.1:8000",
        fetcher,
      }),
    ).resolves.toEqual({ token: "jwt-token" });

    expect(fetcher).toHaveBeenCalledWith("http://127.0.0.1:8000/auth/login", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(loginPayload),
    });
  });

  it("throws ApiError with backend detail when login fails", async () => {
    const fetcher = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ detail: "invalid_credentials" }), {
        status: 401,
        headers: { "Content-Type": "application/json" },
      }),
    );

    await expect(
      login(loginPayload, {
        apiBaseUrl: "http://127.0.0.1:8000",
        fetcher,
      }),
    ).rejects.toMatchObject({
      status: 401,
      detail: "invalid_credentials",
    });
  });

  it("throws ApiError when the network request fails", async () => {
    const fetcher = vi.fn().mockRejectedValue(new Error("offline"));

    await expect(
      login(loginPayload, {
        apiBaseUrl: "http://127.0.0.1:8000",
        fetcher,
      }),
    ).rejects.toMatchObject({
      status: 0,
      detail: "network_error",
    });
  });
});
