import { defineConfig, devices } from "@playwright/test";
import { resolve } from "path";

const repoRoot = resolve(import.meta.dirname, "..");

export default defineConfig({
  testDir: resolve(repoRoot, "tests/e2e/specs"),
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  reporter: "list",
  use: {
    baseURL: "http://localhost:8000",
    trace: "on-first-retry",
    storageState: resolve(repoRoot, "tests/e2e/.auth/user.json"),
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
});
