export const AUTH_TOKEN_STORAGE_KEY = "chat-translation:auth-token";

type TokenStorage = Pick<Storage, "getItem" | "removeItem" | "setItem">;

export function saveAuthToken(
  token: string,
  storage: TokenStorage = window.localStorage,
): void {
  storage.setItem(AUTH_TOKEN_STORAGE_KEY, token);
}

export function getAuthToken(
  storage: TokenStorage = window.localStorage,
): string | null {
  return storage.getItem(AUTH_TOKEN_STORAGE_KEY);
}

export function clearAuthToken(
  storage: TokenStorage = window.localStorage,
): void {
  storage.removeItem(AUTH_TOKEN_STORAGE_KEY);
}

export function hasAuthToken(
  storage: TokenStorage = window.localStorage,
): boolean {
  return getAuthToken(storage) !== null;
}
