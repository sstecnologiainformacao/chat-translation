import { jwtDecode } from "jwt-decode";

export const AUTH_TOKEN_STORAGE_KEY = "chat-translation:auth-token";

type TokenStorage = Pick<Storage, "getItem" | "removeItem" | "setItem">;

export type AuthTokenPayload = {
  exp: number;
  iat: number;
  language: string;
  nickname: string;
};

export type AuthSession = {
  language: string;
  nickname: string;
  token: string;
};

export function saveAuthToken(
  token: string,
  storage: TokenStorage = window.sessionStorage,
): void {
  storage.setItem(AUTH_TOKEN_STORAGE_KEY, token);
}

export function getAuthToken(
  storage: TokenStorage = window.sessionStorage,
): string | null {
  return storage.getItem(AUTH_TOKEN_STORAGE_KEY);
}

export function clearAuthToken(
  storage: TokenStorage = window.sessionStorage,
): void {
  storage.removeItem(AUTH_TOKEN_STORAGE_KEY);
}

export function hasAuthToken(
  storage: TokenStorage = window.sessionStorage,
): boolean {
  return getAuthToken(storage) !== null;
}

export function readAuthTokenPayload(token: string): AuthTokenPayload | null {
  try {
    const payload = jwtDecode<Partial<AuthTokenPayload>>(token);

    if (
      typeof payload.exp === "number" &&
      typeof payload.iat === "number" &&
      typeof payload.language === "string" &&
      typeof payload.nickname === "string"
    ) {
      return {
        exp: payload.exp,
        iat: payload.iat,
        language: payload.language,
        nickname: payload.nickname,
      };
    }
  } catch {
    return null;
  }

  return null;
}

export function getAuthSession(
  storage: TokenStorage = window.sessionStorage,
): AuthSession | null {
  const token = getAuthToken(storage);

  if (token === null) {
    return null;
  }

  const payload = readAuthTokenPayload(token);

  if (payload === null) {
    return null;
  }

  return {
    language: payload.language,
    nickname: payload.nickname,
    token,
  };
}
