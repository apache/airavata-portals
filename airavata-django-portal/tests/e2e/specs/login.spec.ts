import { test, expect } from "../fixtures/auth";

test("authenticated user sees the workspace dashboard", async ({ page }) => {
  await page.goto("/workspace/dashboard/");
  await expect(page.getByRole("heading", { name: /dashboard|projects/i })).toBeVisible();
});

test("logout redirects to the unauth landing page", async ({ page }) => {
  await page.goto("/workspace/dashboard/");
  await page.getByRole("link", { name: /logout/i }).click();
  await expect(page).toHaveURL(/\/$|\/auth\/login/);
});
