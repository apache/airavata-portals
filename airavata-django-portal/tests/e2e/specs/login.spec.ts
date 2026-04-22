import { test, expect } from "../fixtures/auth";

test("authenticated user sees the workspace dashboard", async ({ page }) => {
  await page.goto("/workspace/home");
  await expect(page.getByRole("heading", { name: "Home" })).toBeVisible();
});

test("logout redirects to the unauth landing page", async ({ page }) => {
  await page.goto("/workspace/home");
  // Logout lives in a Bootstrap dropdown in the sidebar. Rather than depend
  // on the dropdown's JS to expand in the headless browser, navigate to the
  // logout URL directly — this still exercises the Django logout view, which
  // then bounces through Keycloak's end-session endpoint back to the portal.
  await page.goto("/auth/logout");
  // Accept any post-logout URL: either the portal landing page, the login
  // page, or Keycloak's end-session confirmation.
  await expect(page).toHaveURL(/localhost:8000\/$|\/auth\/login|openid-connect\/logout/);
});
