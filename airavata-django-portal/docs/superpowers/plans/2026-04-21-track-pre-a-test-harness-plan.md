# Track Pre-A — Test Harness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stand up Vitest (jsdom) + Playwright (storageState-cached auth) infrastructure inside Track C's `tooling/` workspace + `tests/e2e/` at the repo root; fix 5 pre-existing broken tests; ship one showcase test of each type and a contributor doc — all as one squashed commit on `track-pre-a/test-harness`.

**Architecture:** 8 tasks with per-task checkpoint commits that squash to one. Track A will author real test coverage later; Pre-A ships the infra + reference material + the fixed-pre-existing-broken-tests backlog.

**Tech Stack:** Vitest 3 + jsdom + @vue/test-utils 2 / Playwright (chromium) / TypeScript (via Track C's tsconfig.base.json) / npm workspaces.

**Spec:** `docs/superpowers/specs/2026-04-21-track-pre-a-test-harness-design.md`

**Working directory for every command:** `airavata-portals/airavata-django-portal`.

**Starting branch:** `track-pre-a/test-harness`, HEAD at `8570ddecee docs(track-pre-a): test harness design spec`.

---

## File Structure

### New files

- `tooling/vitest.config.js` — `defineVitestConfig({srcDir, overrides})` factory.
- `tooling/vitest-setup.ts` — jsdom polyfills + shared mocks.
- `tooling/playwright.config.ts` — shared Playwright config.
- `django_airavata/apps/{api,admin,workspace}/vitest.config.js` — per-workspace vitest config (3 files).
- `tests/e2e/fixtures/auth.ts` — storageState-caching Playwright fixture.
- `tests/e2e/specs/login.spec.ts` — example Playwright journey (2 tests).
- `django_airavata/apps/workspace/static/django_airavata_workspace/tests/unit/components/project/ProjectListItem.spec.ts` — example Vitest component test.
- `docs/dev/testing.md` — 1-page contributor doc.

### Modified files

- `tooling/package.json` — add `vitest`, `@vitest/ui` (dev-use), `jsdom`, `@vue/test-utils`, `@playwright/test`, `@types/node` to dependencies.
- `package.json` (root) — update `test:e2e` script to run playwright.
- `.gitignore` — add `tests/e2e/.auth/`, `playwright-report/`, `test-results/`.
- 5 pre-existing broken test files: swap `jest.X` → `vi.X`, add any missing imports, fix paths.
- Possibly: `django_airavata/apps/workspace/django-airavata-workspace-plugin-api/package.json` — if the `main`/`module`/`exports` are broken (discovered during test-fix).

---

## Task 1: Vitest infrastructure in `tooling/`

**Files:**
- Create: `tooling/vitest.config.js`
- Create: `tooling/vitest-setup.ts`
- Modify: `tooling/package.json` (add vitest, jsdom, @vue/test-utils deps)

- [ ] **Step 1: Verify clean state**

```bash
cd /Users/yasith/code/artisan/worktree-feat-sdk-and-devenv/airavata-portals/airavata-django-portal
git status --porcelain
git branch --show-current
```
Expected: empty status; branch `track-pre-a/test-harness`.

- [ ] **Step 2: Write `tooling/vitest.config.js`**

```js
import { defineConfig } from "vitest/config";
import vue from "@vitejs/plugin-vue";
import { resolve } from "path";

/**
 * Shared Vitest config factory.
 *
 * @param {object} opts
 * @param {string} opts.srcDir  absolute path to workspace's JS/TS source dir
 * @param {object} [opts.overrides]  shallow-merged over the generated config
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

- [ ] **Step 3: Write `tooling/vitest-setup.ts`**

```ts
// Stubs + polyfills shared by every workspace's Vitest suite.

// The `api` workspace's Session module reads `window.AiravataPortalSessionData`
// at import time; provide a benign default so test-file imports don't crash.
if (typeof window !== "undefined") {
  (window as unknown as { AiravataPortalSessionData?: object }).AiravataPortalSessionData ??= {
    authenticated: false,
  };
}

// Silence the `ResizeObserver is not defined` errors Vue 3 components can
// hit when mounted in jsdom.
if (typeof globalThis.ResizeObserver === "undefined") {
  globalThis.ResizeObserver = class ResizeObserver {
    observe() {}
    unobserve() {}
    disconnect() {}
  };
}
```

- [ ] **Step 4: Add test-harness deps to `tooling/package.json`**

Edit `tooling/package.json` `dependencies` block. Add:

```json
"@playwright/test": "^1.48.0",
"@vue/test-utils": "^2.4.0",
"jsdom": "^25.0.0",
"vitest": "^3.0.0",
```

Keep existing entries. Don't remove anything. Run:

```bash
npm install 2>&1 | tail -5
```
Expected: clean install.

- [ ] **Step 5: Verify tooling/ exports resolve**

```bash
node -e "import('./tooling/vitest.config.js').then(m => console.log('OK defineVitestConfig:', typeof m.defineVitestConfig))"
```
Expected: `OK defineVitestConfig: function`.

- [ ] **Step 6: Checkpoint commit**

```bash
git add tooling/vitest.config.js tooling/vitest-setup.ts tooling/package.json package-lock.json
git commit -m "wip(track-pre-a): vitest infra in tooling/"
```

---

## Task 2: Wire per-workspace `vitest.config.js`

**Files:**
- Create: `django_airavata/apps/api/vitest.config.js`
- Create: `django_airavata/apps/admin/vitest.config.js`
- Create: `django_airavata/apps/workspace/vitest.config.js`

- [ ] **Step 1: Create `api` vitest config**

Write `django_airavata/apps/api/vitest.config.js`:

```js
import { defineVitestConfig } from "@airavata/tooling/vitest.config.js";
import { resolve } from "path";

export default defineVitestConfig({
  srcDir: resolve(import.meta.dirname, "./static/django_airavata_api/js"),
});
```

- [ ] **Step 2: Create `admin` vitest config**

Write `django_airavata/apps/admin/vitest.config.js`:

```js
import { defineVitestConfig } from "@airavata/tooling/vitest.config.js";
import { resolve } from "path";

export default defineVitestConfig({
  srcDir: resolve(import.meta.dirname, "./static/django_airavata_admin/src"),
});
```

- [ ] **Step 3: Create `workspace` vitest config**

Write `django_airavata/apps/workspace/vitest.config.js`:

```js
import { defineVitestConfig } from "@airavata/tooling/vitest.config.js";
import { resolve } from "path";

export default defineVitestConfig({
  srcDir: resolve(import.meta.dirname, "./static/django_airavata_workspace/js"),
});
```

- [ ] **Step 4: Smoke-test (expect failures from existing broken tests)**

Run:
```bash
npm run test 2>&1 | tail -15
```
Expected: vitest runs across workspaces but the 5 existing tests still fail (they'll be fixed in Task 3). Do NOT require exit 0 here — record the current failure count for comparison after Task 3.

- [ ] **Step 5: Checkpoint commit**

```bash
git add django_airavata/apps/api/vitest.config.js \
        django_airavata/apps/admin/vitest.config.js \
        django_airavata/apps/workspace/vitest.config.js
git commit -m "wip(track-pre-a): per-workspace vitest configs"
```

---

## Task 3: Fix 5 pre-existing broken tests

**Files:**
- Modify: `django_airavata/apps/api/static/django_airavata_api/tests/utils/ExperimentUtils.test.js`
- Modify: `django_airavata/apps/api/static/django_airavata_api/tests/models/dependencies/BooleanExpressionEvaluator.test.js`
- Modify: `django_airavata/apps/admin/static/django_airavata_admin/tests/unit/components/statistics/ExperimentStatisticsContainer.spec.js`
- Modify: `django_airavata/apps/workspace/static/django_airavata_workspace/tests/unit/web-components/store.spec.js`
- Modify: `django_airavata/apps/workspace/static/django_airavata_workspace/tests/unit/components/experiment/input-editors/InputEditorContainer.spec.js`
- Possibly: `django_airavata/apps/workspace/django-airavata-workspace-plugin-api/package.json`

### Step 1: Fix `api/tests/utils/ExperimentUtils.test.js`

READ the file first. Apply these mechanical replacements:

- `jest.mock(` → `vi.mock(`
- `jest.resetAllMocks()` → `vi.resetAllMocks()`
- `jest.fn(` → `vi.fn(`
- Any `.mockResolvedValue`, `.mockImplementation`, `.mockReturnValue` stay the same — works in vitest unchanged.

Add this import at the top if any `vi.` call now appears:
```js
import { vi } from "vitest";
```

(With `globals: true` in the vitest config, `vi` may already be global — still, explicit import is safer.)

Run the single spec file:
```bash
cd django_airavata/apps/api && npx vitest run tests/utils/ExperimentUtils.test.js 2>&1 | tail -10
cd - > /dev/null
```
Expected: tests pass (or flag remaining failures).

### Step 2: Fix `api/tests/models/dependencies/BooleanExpressionEvaluator.test.js`

Same `jest` → `vi` replacement. Add `import { vi } from "vitest";` if needed.

Run:
```bash
cd django_airavata/apps/api && npx vitest run tests/models/dependencies/BooleanExpressionEvaluator.test.js 2>&1 | tail -10
cd - > /dev/null
```

### Step 3: Fix `workspace/.../tests/unit/web-components/store.spec.js`

READ the file. It imports from `django-airavata-api` which executes Session.js at import time. Our `vitest-setup.ts` polyfills `window.AiravataPortalSessionData`, so this should just work.

Apply `jest.` → `vi.` if any such calls exist. Add explicit imports as in Step 1.

Run:
```bash
cd django_airavata/apps/workspace && npx vitest run tests/unit/web-components/store.spec.js 2>&1 | tail -10
cd - > /dev/null
```

### Step 4: Fix `workspace/.../tests/unit/components/experiment/input-editors/InputEditorContainer.spec.js`

This one fails because `django-airavata-workspace-plugin-api` doesn't resolve. READ its package.json at `django_airavata/apps/workspace/django-airavata-workspace-plugin-api/package.json` — check `main`, `module`, `exports`, and whether the referenced files exist (Track C's lib-mode vite build outputs to `dist/`; confirm `package.json` points there or to a runnable source entry).

If `main` points to `dist/index.js` but dist is built only on demand, add a fallback: set `main` to `./js/index.js` (or wherever the workspace's runnable source lives). Confirm the file exists.

Run a test build of plugin-api to populate dist if needed:
```bash
cd django_airavata/apps/workspace/django-airavata-workspace-plugin-api && npm run build 2>&1 | tail -3
cd - > /dev/null
```

Then run the test:
```bash
cd django_airavata/apps/workspace && npx vitest run tests/unit/components/experiment/input-editors/InputEditorContainer.spec.js 2>&1 | tail -10
cd - > /dev/null
```

If the test still fails for a reason unrelated to the package resolution (e.g., specific missing mock), fix minimally. If the fix would require substantial refactoring of the test file, STOP and report — option: delete the file and note in the commit message that Track A will re-author.

### Step 5: Fix `admin/.../tests/unit/components/statistics/ExperimentStatisticsContainer.spec.js`

READ the file. Apply `jest.` → `vi.` substitutions. Update any outdated imports (the component uses `formatDate` / `formatIsoDate` from `dates.js` post-Track-B; the test may expect moment output — update mocks if needed).

Run:
```bash
cd django_airavata/apps/admin && npx vitest run tests/unit/components/statistics/ExperimentStatisticsContainer.spec.js 2>&1 | tail -10
cd - > /dev/null
```

### Step 6: Run the full workspace test suite

```bash
npm run test 2>&1 | tail -20
```
Expected: exit 0 (or close — any remaining failures should be documented if they can't be fixed in-scope).

### Step 7: Checkpoint commit

```bash
git add django_airavata/apps/api/static/django_airavata_api/tests/ \
        django_airavata/apps/workspace/static/django_airavata_workspace/tests/ \
        django_airavata/apps/admin/static/django_airavata_admin/tests/ \
        django_airavata/apps/workspace/django-airavata-workspace-plugin-api/package.json 2>/dev/null || true
git commit -m "wip(track-pre-a): fix 5 pre-existing broken vitest tests"
```

---

## Task 4: Example Vitest component test

**Files:**
- Create: `django_airavata/apps/workspace/static/django_airavata_workspace/tests/unit/components/project/ProjectListItem.spec.ts`

- [ ] **Step 1: Read `ProjectListItem.vue`**

Find it at `django_airavata/apps/workspace/static/django_airavata_workspace/js/components/project/ProjectListItem.vue`. Understand its props (expects `project`, with `projectID`, `name`, `description`, `creation_time`, `owner` fields) and text rendering.

- [ ] **Step 2: Write the component test**

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
    // Exact phrasing depends on Intl.RelativeTimeFormat's locale output.
    expect(wrapper.text()).toMatch(/hours? ago/);
  });
});
```

- [ ] **Step 3: Run the test**

```bash
cd django_airavata/apps/workspace && \
  npx vitest run tests/unit/components/project/ProjectListItem.spec.ts 2>&1 | tail -10
cd - > /dev/null
```
Expected: 2 tests passing.

If the test fails because ProjectListItem imports something jsdom doesn't like (e.g., a global plugin), add the specific stub to `tooling/vitest-setup.ts` and re-run.

- [ ] **Step 4: Full test suite**

```bash
npm run test 2>&1 | tail -5
```
Expected: exit 0 — all existing tests plus the new example pass.

- [ ] **Step 5: Checkpoint commit**

```bash
git add django_airavata/apps/workspace/static/django_airavata_workspace/tests/unit/components/project/ProjectListItem.spec.ts
git commit -m "wip(track-pre-a): example Vitest component test (ProjectListItem)"
```

---

## Task 5: Playwright infrastructure in `tooling/` + `tests/e2e/`

**Files:**
- Create: `tooling/playwright.config.ts`
- Create: `tests/e2e/fixtures/auth.ts`
- Create: `tests/e2e/specs/login.spec.ts`

- [ ] **Step 1: Write `tooling/playwright.config.ts`**

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

- [ ] **Step 2: Create `tests/e2e/` scaffolding**

```bash
mkdir -p tests/e2e/specs tests/e2e/fixtures tests/e2e/.auth
```

- [ ] **Step 3: Write `tests/e2e/fixtures/auth.ts`**

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

/**
 * Extended Playwright test that guarantees an authenticated storageState
 * exists before the test runs. If `.auth/user.json` is missing, this fixture
 * drives a real UI login once and saves the state.
 */
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

- [ ] **Step 4: Write `tests/e2e/specs/login.spec.ts`**

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

- [ ] **Step 5: Install Playwright browser binary**

```bash
npx playwright install chromium 2>&1 | tail -5
```
Expected: browser installed.

- [ ] **Step 6: List the Playwright specs (dry run — no browser needed)**

```bash
npx playwright test --config=tooling/playwright.config.ts --list
```
Expected: output lists `login.spec.ts` > `authenticated user sees the workspace dashboard` + `logout redirects to the unauth landing page`.

Note: we do NOT run the actual Playwright tests here — they require `tilt up` to have a live portal at `localhost:8000`, which is out of scope for this subagent dispatch. The operator runs them manually after `tilt up`.

- [ ] **Step 7: Checkpoint commit**

```bash
git add tooling/playwright.config.ts tests/e2e/
git commit -m "wip(track-pre-a): Playwright infra + login.spec.ts example journey"
```

---

## Task 6: Root scripts + .gitignore + contributor doc

**Files:**
- Modify: `package.json` (root) — update `test:e2e` script.
- Modify: `.gitignore` — add Playwright artifacts and .auth/.
- Create: `docs/dev/testing.md`.

- [ ] **Step 1: Update root `test:e2e` script**

Edit root `package.json`. Find the line:

```json
"test:e2e": "echo 'test:e2e placeholder — wired up in Track Pre-A'"
```

Replace with:

```json
"test:e2e": "playwright test --config=tooling/playwright.config.ts"
```

- [ ] **Step 2: Update `.gitignore`**

Append to `.gitignore`:

```
# Playwright (Track Pre-A)
tests/e2e/.auth/
playwright-report/
test-results/
```

- [ ] **Step 3: Write `docs/dev/testing.md`**

```bash
mkdir -p docs/dev
```

```markdown
# Testing the Airavata Django Portal

The monorepo ships with two test harnesses set up by Track Pre-A
(`docs/superpowers/specs/2026-04-21-track-pre-a-test-harness-design.md`):

- **Vitest** for fast component and utility tests (jsdom environment,
  `@vue/test-utils`).
- **Playwright** for end-to-end journeys (chromium, `storageState`-cached
  Keycloak auth).

## Running tests

| Command | What it does |
|---|---|
| `npm run test` | Runs Vitest across every workspace that has a `vitest.config.js`. |
| `npm run test:e2e` | Runs Playwright against whatever is serving at `localhost:8000`. Requires `tilt up` to be running first. |

## Adding a Vitest component test

Location: `django_airavata/apps/<workspace>/static/django_airavata_<label>/tests/unit/<path>/<Component>.spec.ts`.

Reference: `django_airavata/apps/workspace/static/django_airavata_workspace/tests/unit/components/project/ProjectListItem.spec.ts`.

```ts
import { describe, test, expect } from "vitest";
import { mount } from "@vue/test-utils";
import MyComponent from "@/components/whatever/MyComponent.vue";

describe("MyComponent", () => {
  test("renders something", () => {
    const wrapper = mount(MyComponent, { props: { /* ... */ } });
    expect(wrapper.text()).toContain("...");
  });
});
```

If the component pulls a global API that jsdom doesn't provide (e.g.
`ResizeObserver`, `matchMedia`), polyfill it in `tooling/vitest-setup.ts`
rather than mocking per-test.

## Adding a Playwright journey

Location: `tests/e2e/specs/<slug>.spec.ts`.

Reference: `tests/e2e/specs/login.spec.ts`.

```ts
import { test, expect } from "../fixtures/auth";

test("my journey", async ({ page }) => {
  await page.goto("/workspace/dashboard/");
  // assert / interact
});
```

The `auth` fixture ensures the test runs as an authenticated user; to run
an *unauthenticated* journey, import from `@playwright/test` directly
instead of `../fixtures/auth`.

## Regenerating `tests/e2e/.auth/user.json`

Keycloak session tokens expire. When Playwright fails with an auth error,
delete the cached state and re-run:

```sh
rm -rf tests/e2e/.auth
npm run test:e2e
```

The fixture will drive one real UI login and rebuild the state file.

## Environment variables

- `AIRAVATA_TEST_USER` — Keycloak username (default `default-admin`).
- `AIRAVATA_TEST_PASSWORD` — Keycloak password (default `123456`).
- `CI` — when set, Playwright runs with `retries: 2` and `forbidOnly: true`.

## Prereqs

- `tilt up` running (portal served at `localhost:8000`, Keycloak at `localhost:18080`).
- `npx playwright install chromium` has been run once on the machine.
```

- [ ] **Step 4: Verify doc length**

```bash
wc -l docs/dev/testing.md
```
Expected: ≥ 30 lines.

- [ ] **Step 5: Checkpoint commit**

```bash
git add package.json .gitignore docs/dev/testing.md
git commit -m "wip(track-pre-a): root test:e2e script + .gitignore + contributor doc"
```

---

## Task 7: Run every gate check

**Files:** none (verification only).

- [ ] **Step 1: Gates 1-7 (structural)**

```bash
echo "=== G1 ===" && \
test -f tooling/vitest.config.js && test -f tooling/vitest-setup.ts && test -f tooling/playwright.config.ts && echo OK-1

echo "=== G2 ===" && \
python3 -c "
import json
d = json.load(open('tooling/package.json'))
assert '@playwright/test' in d.get('dependencies', {}), 'missing @playwright/test'
print('OK-2')
"

echo "=== G3 ===" && \
for ws in django_airavata/apps/api django_airavata/apps/workspace django_airavata/apps/admin; do
  test -f "$ws/vitest.config.js" && grep -q "@airavata/tooling/vitest.config.js" "$ws/vitest.config.js" || { echo "FAIL $ws"; exit 1; }
done
echo OK-3

echo "=== G4 ===" && \
test -d tests/e2e/specs && test -d tests/e2e/fixtures && test -f tests/e2e/fixtures/auth.ts && test -f tests/e2e/specs/login.spec.ts && echo OK-4

echo "=== G5 ===" && \
grep -q "tests/e2e/\.auth" .gitignore && echo OK-5

echo "=== G6 ===" && \
python3 -c "
import json
s = json.load(open('package.json'))['scripts']['test:e2e']
assert 'playwright' in s, f'test:e2e script: {s!r}'
print('OK-6')
"

echo "=== G7 ===" && \
test -f django_airavata/apps/workspace/static/django_airavata_workspace/tests/unit/components/project/ProjectListItem.spec.ts && echo OK-7
```

- [ ] **Step 2: Gate 8 — npm run test exits 0**

```bash
npm run test 2>&1 | tail -10
echo "exit=$?"
```
Expected: exit 0; at least 6 test files execute (5 pre-existing + new example).

- [ ] **Step 3: Gate 9 — Playwright spec listing**

```bash
npx playwright test --config=tooling/playwright.config.ts --list
```
Expected: output lists `login.spec.ts` with 2 tests.

- [ ] **Step 4: Gate 10 — contributor doc**

```bash
test -f docs/dev/testing.md && test $(wc -l < docs/dev/testing.md) -ge 30 && echo OK-10
```

- [ ] **Step 5: Gate 11 — additive-only guardrail**

```bash
git diff --name-only modernization..HEAD \
  | grep -vE "^(airavata-django-portal/)?(tooling/|tests/e2e/|docs/dev/|docs/superpowers/|django_airavata/apps/(api|admin|workspace)/.*\.(test|spec)\.(js|ts)$|.*/vitest\.config\.js$|package\.json$|package-lock\.json$|\.gitignore$)" \
  | head
```
Expected: empty — only test/config/docs/package files changed.

If any unexpected file shows up (e.g. a source file outside `/tests/`), investigate before squashing.

---

## Task 8: Squash and merge

- [ ] **Step 1: Verify checkpoint commits**

```bash
git log --oneline -10
```
Expected: 6 `wip(track-pre-a):` commits on top of `8570ddecee docs(track-pre-a): test harness design spec`.

- [ ] **Step 2: Soft-reset to the spec commit**

```bash
git reset --soft 8570ddecee
git diff --cached --stat | tail -5
```

- [ ] **Step 3: Create the squashed commit**

```bash
git commit -m "$(cat <<'EOF'
chore(portal): test harness scaffolding

Track Pre-A of the portal modernization umbrella. Scaffolding-only MVP
that gives Track A a safety net before the Vue 3 Composition + TypeScript
rewrite of 178 .vue files.

Vitest (jsdom, @vue/test-utils) infrastructure:
- tooling/vitest.config.js exports defineVitestConfig({srcDir, overrides}).
- tooling/vitest-setup.ts polyfills window.AiravataPortalSessionData +
  ResizeObserver so api workspace's Session.js import doesn't crash.
- Per-workspace vitest.config.js in api / admin / workspace.

Playwright (storageState-cached auth):
- tooling/playwright.config.ts, testDir=tests/e2e/specs, single chromium
  project, serial execution, baseURL localhost:8000.
- tests/e2e/fixtures/auth.ts — extended test that drives one UI-login
  round trip and caches storageState to tests/e2e/.auth/user.json.
- tests/e2e/specs/login.spec.ts — 2-test example journey
  (authed dashboard + logout redirect).

Fixed 5 pre-existing broken tests so npm run test now exits 0:
- api/.../ExperimentUtils.test.js (jest.X → vi.X)
- api/.../BooleanExpressionEvaluator.test.js (jest.X → vi.X)
- workspace/.../store.spec.js (fixed by vitest-setup polyfill)
- workspace/.../InputEditorContainer.spec.js (plugin-api package main fix)
- admin/.../ExperimentStatisticsContainer.spec.js (jest.X → vi.X +
  dates.js mock update)

Example Vitest component test: ProjectListItem.spec.ts (2 tests).

Root scripts: test:e2e now runs
`playwright test --config=tooling/playwright.config.ts`.
.gitignore: tests/e2e/.auth/, playwright-report/, test-results/.

Contributor doc: docs/dev/testing.md — 1 page covering vitest + playwright
patterns, auth-state regeneration, env overrides.

No CI integration yet (Track A or later). No existing source files
modified outside the test/config/docs footprint.

Spec: docs/superpowers/specs/2026-04-21-track-pre-a-test-harness-design.md
EOF
)"
```

- [ ] **Step 4: Push + merge**

```bash
git push -u origin track-pre-a/test-harness
git checkout modernization
git pull origin modernization
git merge --no-ff track-pre-a/test-harness -m "merge: Track Pre-A (test harness)"
git push origin modernization
```

- [ ] **Step 5: Verify merge**

```bash
git log --oneline --merges -5
```
Expected: top is `merge: Track Pre-A (test harness)`, then Track B, Track C, Track D, amisha merge.

---

## Plan Self-Review

**Spec coverage:**

| Spec section | Plan task |
|---|---|
| Shared Vitest infra in tooling/ | Task 1 |
| Per-workspace vitest configs | Task 2 |
| Fix 5 pre-existing broken tests | Task 3 |
| Example component test | Task 4 |
| Shared Playwright infra | Task 5 |
| tests/e2e/ layout + fixture + spec | Task 5 |
| Root scripts + .gitignore + doc | Task 6 |
| Done criteria (11 gates) | Task 7 |
| Squash + merge | Task 8 |

Every spec requirement maps to a task.

**Placeholder scan:** no TBD/TODO/FIXME. Every step has concrete code or shell commands.

**Type consistency:** branch `track-pre-a/test-harness`, paths, `defineVitestConfig` signature, `storageState` file location, `auth.ts` fixture export consistent between spec and plan.

---

## Execution handoff

Plan complete and saved to `airavata-django-portal/docs/superpowers/plans/2026-04-21-track-pre-a-test-harness-plan.md`. Recommended execution: `superpowers:subagent-driven-development`.
