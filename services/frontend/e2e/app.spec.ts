import { expect, test } from "@playwright/test";

test("shows the initial login and public room preview", async ({ page }) => {
  await page.goto("/");

  await expect(
    page.getByRole("heading", { name: "Join the room" }),
  ).toBeVisible();
  await expect(page.getByLabel("Deploy email")).toBeVisible();
  await expect(page.getByLabel("Password")).toBeVisible();
  await expect(page.getByRole("button", { name: /continue/i })).toBeVisible();
  await expect(page.getByText("Public room")).toBeVisible();
  await expect(page.getByText("Live translation preview")).toBeVisible();

  await page.getByLabel("Deploy email").fill("joao@deploy.co");
  await page.getByLabel("Password").fill("local-pass");

  await expect(page.getByLabel("Deploy email")).toHaveValue("joao@deploy.co");

  await page.getByRole("button", { name: "Create a new account" }).click();

  await expect(
    page.getByRole("heading", { name: "Create account" }),
  ).toBeVisible();
  await expect(page.getByLabel("Deploy email")).toBeVisible();
  await expect(page.getByLabel("Password")).toBeVisible();
  await expect(page.getByLabel("Nickname")).toBeVisible();
  await expect(page.getByLabel("Language")).toBeVisible();

  await page.getByLabel("Nickname").fill("joao");
  await page.getByLabel("Language").selectOption("Portuguese");

  await expect(page.getByLabel("Language")).toHaveValue("Portuguese");
});
