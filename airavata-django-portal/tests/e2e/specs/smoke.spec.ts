import { test, expect } from "../fixtures/auth";

const AUTHENTICATED_PAGES = [
  "/workspace/home",
  "/workspace/launch",
  "/workspace/projects",
  "/workspace/applications",
  "/workspace/datasets",
  "/workspace/storage",
  "/workspace/compute",
  "/admin/applications/",
  "/admin/credentials/",
  "/admin/experiment-statistics/",
  "/admin/gateway-resource-profile/",
  "/admin/notices/",
  "/admin/users/",
  "/admin/extended-user-profile/",
  "/dataparsers/",
];

// Errors that routinely appear in a healthy portal (third-party warnings,
// missing favicons on non-prod, keycloak redirects, etc.) and should not fail
// the smoke pass. This file's purpose is to catch Vue/TS regressions from
// the modernization rewrite — not to cover Airavata-server issues that
// surface as API 4xx/5xx in a local dev stack.
const IGNORED_ERROR_PATTERNS = [
  /favicon/i,
  /ResizeObserver loop/i,
  /Non-Error promise rejection captured/i,
  // Airavata dev stack often returns 403/501 on admin APIs the local
  // Keycloak user lacks privileges for, or that aren't implemented against
  // the bundled test gateway. These are not frontend regressions.
  /Failed to load resource: the server responded with a status of (401|403|500|501|503)/,
  /This feature is not yet available/i,
];

for (const path of AUTHENTICATED_PAGES) {
  test(`renders ${path} without console errors`, async ({ page }) => {
    const errors: string[] = [];
    const isIgnored = (text: string) => IGNORED_ERROR_PATTERNS.some((p) => p.test(text));
    page.on("pageerror", (err) => {
      if (isIgnored(err.message)) return;
      errors.push(`pageerror: ${err.message}`);
    });
    page.on("console", (msg) => {
      if (msg.type() !== "error") return;
      const text = msg.text();
      if (isIgnored(text)) return;
      errors.push(`console: ${text}`);
    });

    const response = await page.goto(path);
    expect(response?.status(), `HTTP status for ${path}`).toBeLessThan(400);
    // Give SPA bundles a moment to hydrate before asserting clean console.
    await page.waitForLoadState("networkidle", { timeout: 10_000 }).catch(() => {});
    expect(errors, `Console errors on ${path}`).toEqual([]);
  });
}
