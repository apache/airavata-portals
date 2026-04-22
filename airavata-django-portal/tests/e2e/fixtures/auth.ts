import { test as base, expect, type Page } from "@playwright/test";
import { existsSync, mkdirSync } from "node:fs";
import { dirname, resolve } from "node:path";

const STATE_FILE = resolve(import.meta.dirname, "../.auth/user.json");

async function uiLogin(page: Page): Promise<void> {
  const username = process.env.AIRAVATA_TEST_USER ?? "default-admin";
  const password = process.env.AIRAVATA_TEST_PASSWORD ?? "123456";
  await page.goto("/auth/login");
  await page
    .getByRole("link", { name: /username.*password|keycloak/i })
    .click()
    .catch(() => {});
  await page.fill('input[name="username"]', username);
  await page.fill('input[name="password"]', password);
  await page.click('button[type="submit"]');
  await expect(page).toHaveURL(/\/workspace/);
}

export const test = base.extend({
  storageState: async ({ browser }, use) => {
    if (!existsSync(STATE_FILE)) {
      mkdirSync(dirname(STATE_FILE), { recursive: true });
      const context = await browser.newContext();
      const page = await context.newPage();
      await uiLogin(page);
      await context.storageState({ path: STATE_FILE });
      await context.close();
    }
    await use(STATE_FILE);
  },
});

export { expect };
