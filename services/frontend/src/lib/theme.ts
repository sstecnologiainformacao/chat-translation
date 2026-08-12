export const THEME_STORAGE_KEY = "chat-translation:theme";

export type Theme = "dark" | "light";

type ThemeStorage = Pick<Storage, "getItem" | "setItem">;

export function getStoredTheme(storage = getBrowserStorage()): Theme {
  if (!hasGetItem(storage)) {
    return "light";
  }

  return parseTheme(storage.getItem(THEME_STORAGE_KEY));
}

export function saveTheme(
  theme: Theme,
  storage = getBrowserStorage(),
): void {
  if (!hasSetItem(storage)) {
    return;
  }

  storage.setItem(THEME_STORAGE_KEY, theme);
}

export function applyTheme(
  theme: Theme,
  element: Pick<DOMTokenList, "toggle"> = document.documentElement.classList,
): void {
  element.toggle("dark", theme === "dark");
}

export function getNextTheme(theme: Theme): Theme {
  return theme === "dark" ? "light" : "dark";
}

function parseTheme(value: string | null): Theme {
  return value === "dark" ? "dark" : "light";
}

function getBrowserStorage(): unknown {
  return typeof window === "undefined" ? null : window.localStorage;
}

function hasGetItem(storage: unknown): storage is Pick<ThemeStorage, "getItem"> {
  return (
    typeof storage === "object" &&
    storage !== null &&
    "getItem" in storage &&
    typeof storage.getItem === "function"
  );
}

function hasSetItem(storage: unknown): storage is Pick<ThemeStorage, "setItem"> {
  return (
    typeof storage === "object" &&
    storage !== null &&
    "setItem" in storage &&
    typeof storage.setItem === "function"
  );
}
