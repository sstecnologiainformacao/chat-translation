import { describe, expect, it } from "vitest";

import {
  clearAuthToken,
  getAuthToken,
  hasAuthToken,
  saveAuthToken,
} from "@/lib/auth";

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
