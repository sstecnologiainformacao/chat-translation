import { expect, test } from "@playwright/test";

test("shows the initial login and public room preview", async ({ page }) => {
  await page.goto("/");

  await expect(
    page.getByRole("heading", { name: "Join the room" }),
  ).toBeVisible();
  await expect(page.getByLabel("Username")).toBeVisible();
  await expect(page.getByLabel("Password")).toBeVisible();
  await expect(page.getByLabel("Nickname")).toBeVisible();
  await expect(page.getByLabel("Language")).toBeVisible();
  await expect(page.getByRole("button", { name: /continue/i })).toBeVisible();
  await expect(page.getByText("Public room")).toBeVisible();
  await expect(page.getByText("Live translation preview")).toBeVisible();

  await page.getByLabel("Username").fill("local-user");
  await page.getByLabel("Password").fill("local-pass");
  await page.getByLabel("Nickname").fill("joao");
  await page.getByLabel("Language").fill("Portuguese");

  await expect(page.getByLabel("Language")).toHaveValue("Portuguese");
});
