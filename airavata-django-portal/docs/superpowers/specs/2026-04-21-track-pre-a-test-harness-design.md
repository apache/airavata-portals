# Track Pre-A — Test Harness Design

> Track Pre-A of the portal modernization umbrella. Umbrella spec:
> `docs/superpowers/specs/2026-04-21-portal-modernization-design.md`.

## Goal

Stand up Vitest (jsdom) + Playwright (storageState-cached auth) infrastructure
in Track C's `tooling/` workspace so Track A has a safety net while rewriting
178 `.vue` files. Ship a **scaffolding-only MVP**: one showcase test of each
type, fix the 5 pre-existing broken tests, wire the root scripts, and produce
a 1-page contributor doc. No CI integration yet; Track A authors real test
coverage as it rewrites files.

## Scope

One squashed commit on `track-pre-a/test-harness`.

### 1. Shared Vitest infrastructure in `tooling/`

- `tooling/vitest.config.js` exports `defineVitestConfig({ srcDir, overrides })`
  factory. jsdom environment, `globals: true`, auto-loaded setup file.
- `tooling/vitest-setup.ts` polyfills `window.AiravataPortalSessionData`
  (the `api` workspace's Session.js reads it at import time) and
  `ResizeObserver` (Vue 3 components sometimes hit it in jsdom).
- Per-workspace `vitest.config.js` becomes a 3-line call to
  `defineVitestConfig({ srcDir })`.

### 2. Shared Playwright infrastructure in `tooling/`

- `tooling/playwright.config.ts` — `testDir: "../tests/e2e/specs"`, single
  Chromium project, `storageState: "../tests/e2e/.auth/user.json"`, serial
  execution (shared Keycloak session state).
- `@playwright/test` added as a dev dep of `tooling/`.
- Root `"test:e2e"` script becomes:
  `playwright test --config=tooling/playwright.config.ts`.

### 3. `tests/e2e/` at repo root

- `tests/e2e/fixtures/auth.ts` — extended Playwright `test` that guarantees
  an authenticated `storageState`. If `.auth/user.json` is missing, the
  fixture drives a real UI-driven Keycloak login once and saves the state.
  Env overrides: `AIRAVATA_TEST_USER`, `AIRAVATA_TEST_PASSWORD`.
- `tests/e2e/specs/login.spec.ts` — two example journeys: authed dashboard
  load, and logout redirect.
- `tests/e2e/.auth/` — gitignored; holds `user.json`.

### 4. Showcase Vitest component test

`django_airavata/apps/workspace/static/django_airavata_workspace/tests/unit/components/project/ProjectListItem.spec.ts`
mounts `ProjectListItem` with a fake project and asserts name + relative-time
rendering. Serves as the Track A reference for "how to write a component
test against this codebase".

### 5. Fix 5 pre-existing broken tests

Bring these under the new Vitest setup so `npm run test` exits 0:

- `django_airavata/apps/api/static/django_airavata_api/tests/utils/ExperimentUtils.test.js`
  — swap `jest.resetAllMocks()` → `vi.resetAllMocks()`; `jest.mock` → `vi.mock`.
- `django_airavata/apps/api/static/django_airavata_api/tests/models/dependencies/BooleanExpressionEvaluator.test.js`
  — same jest → vi swap; relies on `globals: true`.
- `django_airavata/apps/admin/static/django_airavata_admin/tests/unit/components/statistics/ExperimentStatisticsContainer.spec.js`
  — may need updates to import paths + mock shape; verify + fix.
- `django_airavata/apps/workspace/static/django_airavata_workspace/tests/unit/web-components/store.spec.js`
  — fixed by the shared `vitest-setup.ts` polyfill (`window.AiravataPortalSessionData`).
- `django_airavata/apps/workspace/.../tests/unit/components/experiment/input-editors/InputEditorContainer.spec.js`
  — fix `django-airavata-workspace-plugin-api` entry resolution (the
  workspace package's `"main"` may point to a non-existent file after
  Track C's vite switch; adjust its `package.json` or add a `"main"`).

### 6. Contributor doc

`docs/dev/testing.md` — 1-page guide covering:
- How to add a Vitest spec (path convention + reference to
  `ProjectListItem.spec.ts`).
- How to add a Playwright journey (fixture import + reference to
  `login.spec.ts`).
- How to regenerate `.auth/user.json` (delete file; re-run `npm run test:e2e`).
- Environment: `tilt up` must be running; `AIRAVATA_TEST_USER` /
  `AIRAVATA_TEST_PASSWORD` env overrides.

### 7. Root scripts

- `package.json` `"test"` — already via `npm run test --workspaces --if-present`
  (Track C). No change needed.
- `package.json` `"test:e2e"` — change from the placeholder echo to
  `playwright test --config=tooling/playwright.config.ts`.

### 8. `.gitignore` additions

- `tests/e2e/.auth/` (generated credentials).
- `playwright-report/`, `test-results/` (Playwright run artifacts).

## Out of scope

- The full umbrella's 25 component suites + 12 journeys. Track A authors
  real coverage as it rewrites files.
- CI integration. Track Pre-A ships the scripts; wiring to `.github/workflows/`
  happens later.
- Visual-regression testing.
- Accessibility-axe integration.

## Design decisions

| # | Decision | Alternatives |
|---|---|---|
| Q1 | Scaffolding-only MVP (1 component test + 1 journey + fix broken 5 + docs) | Full umbrella scope (25+12); deep-dive reference material |
| Q2 | All shared test infra in `tooling/` workspace | `tests/` workspace at root; mixed vitest-in-tooling + playwright-at-root |
| Q3 | Playwright specs at `tests/e2e/` root; config in `tooling/` | Everything under `tooling/playwright/`; fully conventional root layout |
| Q4 | `storageState` cached auth (`.auth/user.json`) | Keycloak ROPC at fixture setup; full UI login every test |
| Q5 | Showcase + fix 5 existing broken tests | Showcase only; deep-dive per test type |
| Q6 | No CI integration in Pre-A | Vitest + Playwright both in CI; Vitest only |
| Q7 | jsdom | happy-dom |
| Q8 | One squashed commit | Two commits (vitest infra; Playwright infra) |

## Key code artifacts

### `tooling/vitest.config.js`

```js
import { defineConfig } from "vitest/config";
import vue from "@vitejs/plugin-vue";
import { resolve } from "path";

/**
 * Shared Vitest config factory.
 *
 * @param {object} opts
 * @param {string} opts.srcDir  absolute path to workspace's JS/TS source dir
 * @param {object} [opts.overrides]
 */
export function defineVitestConfig({ srcDir, overrides = {} }) {
  return defineConfig({
    plugins: [vue()],
    resolve: {
      alias: { "@": srcDir },
      extensions: [".vue", ".ts", ".js", ".json"],
    },
    test: {
      globals: true,
      environment: "jsdom",
      setupFiles: [resolve(import.meta.dirname, "./vitest-setup.ts")],
      include: ["**/*.{test,spec}.{js,ts,mjs}", "**/tests/**/*.{test,spec}.{js,ts}"],
      exclude: ["**/node_modules/**", "**/dist/**", "**/tests/e2e/**"],
      clearMocks: true,
      restoreMocks: true,
    },
    ...overrides,
  });
}
```

### `tooling/vitest-setup.ts`

```ts
if (typeof window !== "undefined") {
  (window as unknown as { AiravataPortalSessionData?: object }).AiravataPortalSessionData ??= {
    authenticated: false,
  };
}

if (typeof globalThis.ResizeObserver === "undefined") {
  globalThis.ResizeObserver = class ResizeObserver {
    observe() {}
    unobserve() {}
    disconnect() {}
  };
}
```

### `tooling/playwright.config.ts`

```ts
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
```

### `tests/e2e/fixtures/auth.ts`

```ts
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
```

### `tests/e2e/specs/login.spec.ts`

```ts
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
```

### Example Vitest component spec

`django_airavata/apps/workspace/static/django_airavata_workspace/tests/unit/components/project/ProjectListItem.spec.ts`:

```ts
import { describe, test, expect } from "vitest";
import { mount } from "@vue/test-utils";
import ProjectListItem from "@/components/project/ProjectListItem.vue";

describe("ProjectListItem", () => {
  const project = {
    projectID: "proj-1",
    name: "My Project",
    description: "Sample project",
    creation_time: new Date(Date.now() - 3 * 3600_000).toISOString(),
    owner: "testuser",
  };

  test("renders the project name", () => {
    const wrapper = mount(ProjectListItem, { props: { project } });
    expect(wrapper.text()).toContain("My Project");
  });

  test("renders a relative creation time", () => {
    const wrapper = mount(ProjectListItem, { props: { project } });
    expect(wrapper.text()).toMatch(/hours? ago/);
  });
});
```

### Per-workspace `vitest.config.js` pattern

```js
import { defineVitestConfig } from "@airavata/tooling/vitest.config.js";
import { resolve } from "path";

export default defineVitestConfig({
  srcDir: resolve(import.meta.dirname, "<workspace's JS source dir>"),
});
```

## Done criteria (gate checks)

Umbrella plan's Task 3 Step 11 runs these:

```bash
# 1. tooling/ Vitest + Playwright infra.
test -f tooling/vitest.config.js \
  && test -f tooling/vitest-setup.ts \
  && test -f tooling/playwright.config.ts

# 2. @playwright/test is a devDep of tooling/.
python3 -c "
import json
d = json.load(open('tooling/package.json'))
assert '@playwright/test' in d.get('dependencies', {})
print('OK')
"

# 3. Per-workspace vitest.config.js wired.
for ws in django_airavata/apps/api django_airavata/apps/workspace django_airavata/apps/admin; do
  test -f "$ws/vitest.config.js" \
    && grep -q "@airavata/tooling/vitest.config.js" "$ws/vitest.config.js" \
    || { echo "FAIL $ws"; exit 1; }
done

# 4. tests/e2e/ structure.
test -d tests/e2e/specs \
  && test -d tests/e2e/fixtures \
  && test -f tests/e2e/fixtures/auth.ts \
  && test -f tests/e2e/specs/login.spec.ts

# 5. .auth/ is gitignored.
grep -q "tests/e2e/\.auth" .gitignore

# 6. test:e2e runs Playwright.
python3 -c "
import json
s = json.load(open('package.json'))['scripts']['test:e2e']
assert 'playwright' in s
"

# 7. Example component test.
test -f django_airavata/apps/workspace/static/django_airavata_workspace/tests/unit/components/project/ProjectListItem.spec.ts

# 8. npm run test exits 0.
npm run test

# 9. Playwright lists the example spec.
npx playwright install chromium
npx playwright test --config=tooling/playwright.config.ts --list

# 10. Contributor doc exists.
test -f docs/dev/testing.md \
  && test $(wc -l < docs/dev/testing.md) -ge 30

# 11. Additive-only guardrail: only test/config/docs/package files changed.
git diff --name-only modernization..HEAD \
  | grep -vE "^(tooling/|tests/e2e/|docs/dev/|docs/superpowers/|django_airavata/apps/(api|admin|workspace)/.*\.(test|spec)\.(js|ts)$|.*/vitest\.config\.js$|package\.json$|package-lock\.json$|\.gitignore$)" \
  | head
# Expected: empty.
```

## Risks and mitigations

| Risk | Mitigation |
|---|---|
| Playwright UI selectors don't match the real portal's login DOM | Forgiving regexes + fail-fast on first mismatch |
| `.auth/user.json` expires | Fixture detects missing file; operator deletes on expiry; documented in `docs/dev/testing.md` |
| 5 existing broken tests need deep refactoring | Downgrade scope: delete; note in commit message; Track A re-authors |
| jsdom missing an API used at import time | `vitest-setup.ts` adds polyfills; first-miss pattern documented |
| `@airavata/tooling` can't export `.ts` directly for Playwright | Playwright compiles TS in-process via esbuild; no build step needed |
| ROPC env credentials drift from dev defaults | Env-var overrides documented in contributor doc |
