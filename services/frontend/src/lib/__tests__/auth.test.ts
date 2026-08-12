import { describe, expect, it } from "vitest";

import {
  clearAuthToken,
  getAuthSession,
  getAuthToken,
  hasAuthToken,
  readAuthTokenPayload,
  saveAuthToken,
} from "@/lib/auth";

const tokenWithProfile =
  "eyJhbGciOiJIUzI1NiJ9.eyJuaWNrbmFtZSI6ImpvYW8iLCJsYW5ndWFnZSI6IlBvcnR1Z3Vlc2UiLCJpYXQiOjEsImV4cCI6Mn0.signature";

describe("auth token storage", () => {
  it("stores and reads the auth token", () => {
    const storage = createTokenStorage();

    saveAuthToken("jwt-token", storage);

    expect(getAuthToken(storage)).toBe("jwt-token");
    expect(hasAuthToken(storage)).toBe(true);
  });

  it("clears the auth token", () => {
    const storage = createTokenStorage();

    saveAuthToken("jwt-token", storage);

    clearAuthToken(storage);

    expect(getAuthToken(storage)).toBeNull();
    expect(hasAuthToken(storage)).toBe(false);
  });

  it("reads the profile fields from a JWT payload", () => {
    expect(readAuthTokenPayload(tokenWithProfile)).toEqual({
      exp: 2,
      iat: 1,
      language: "Portuguese",
      nickname: "joao",
    });
  });

  it("returns null when the JWT payload cannot be read", () => {
    expect(readAuthTokenPayload("not-a-token")).toBeNull();
  });

  it("builds an auth session from a stored token", () => {
    const storage = createTokenStorage();

    saveAuthToken(tokenWithProfile, storage);

    expect(getAuthSession(storage)).toEqual({
      language: "Portuguese",
      nickname: "joao",
      token: tokenWithProfile,
    });
  });
});

function createTokenStorage() {
  const values = new Map<string, string>();

  return {
    getItem: (key: string) => values.get(key) ?? null,
    removeItem: (key: string) => {
      values.delete(key);
    },
    setItem: (key: string, value: string) => {
      values.set(key, value);
    },
  };
}
