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
