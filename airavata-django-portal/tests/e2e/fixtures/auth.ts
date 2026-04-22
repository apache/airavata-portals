import { test as base, expect, type Page } from "@playwright/test";
import { existsSync, mkdirSync } from "node:fs";
import { dirname, resolve } from "node:path";

const STATE_FILE = resolve(import.meta.dirname, "../.auth/user.json");

async function uiLogin(page: Page): Promise<void> {
  const username = process.env.AIRAVATA_TEST_USER ?? "default-admin";
  const password = process.env.AIRAVATA_TEST_PASSWORD ?? "123456";
  await page.goto("/auth/login");
  // Django may render an intermediate "pick your IdP" page. Short-circuit
  // the link click so we fall through to the Keycloak form if the link is
  // absent (e.g. only one IdP configured and Django redirects directly).
  await page
    .getByRole("link", { name: /username.*password|keycloak/i })
    .click({ timeout: 1000 })
    .catch(() => {});
  await page.fill('input[name="username"]', username);
  await page.fill('input[name="password"]', password);
  await page.click('#kc-login, button[type="submit"]');
  await expect(page).toHaveURL(/\/workspace/);
}

export const test = base.extend({
  storageState: async ({ browser, baseURL }, use) => {
    if (!existsSync(STATE_FILE)) {
      mkdirSync(dirname(STATE_FILE), { recursive: true });
      const context = await browser.newContext({ baseURL });
      const page = await context.newPage();
      await uiLogin(page);
      await context.storageState({ path: STATE_FILE });
      await context.close();
    }
    await use(STATE_FILE);
  },
});

export { expect };
