import { describe, expect, it, vi } from "vitest";

import {
  applyTheme,
  getNextTheme,
  getStoredTheme,
  saveTheme,
  THEME_STORAGE_KEY,
} from "@/lib/theme";

describe("theme helpers", () => {
  it("defaults to light when no stored theme exists", () => {
    const storage = createThemeStorage();

    expect(getStoredTheme(storage)).toBe("light");
  });

  it("reads and stores the selected theme", () => {
    const storage = createThemeStorage();

    saveTheme("dark", storage);

    expect(storage.getItem(THEME_STORAGE_KEY)).toBe("dark");
    expect(getStoredTheme(storage)).toBe("dark");
  });

  it("toggles the dark class on the document element", () => {
    const classList = { toggle: vi.fn() };

    applyTheme("dark", classList);
    applyTheme("light", classList);

    expect(classList.toggle).toHaveBeenNthCalledWith(1, "dark", true);
    expect(classList.toggle).toHaveBeenNthCalledWith(2, "dark", false);
  });

  it("returns the opposite theme", () => {
    expect(getNextTheme("dark")).toBe("light");
    expect(getNextTheme("light")).toBe("dark");
  });
});

function createThemeStorage() {
  const values = new Map<string, string>();

  return {
    getItem: (key: string) => values.get(key) ?? null,
    setItem: (key: string, value: string) => {
      values.set(key, value);
    },
  };
}
