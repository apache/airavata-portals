# Airavata Django Portal — Modernization Umbrella Spec

**Date:** 2026-04-21
**Status:** Approved (awaiting per-track brainstorms)
**Shape:** Roadmap + guardrails. This document commits the scope, sequencing, and cross-track constraints. Each track gets its own per-track brainstorm → design spec → implementation plan → code.

## Context

The portal (`airavata-django-portal`) runs on a mostly modern baseline: Python 3.12 / Django 5.1 / DRF 3.15 / Wagtail 6.3 / uvicorn[standard] / pytest / ruff + ty / Vite 6 / Yarn workspaces / Vitest / Vue 3. SQLite sessions run in WAL mode after the dev-env stabilisation pass. What remains is a collection of legacy residues that still cause real pain — Vue 2 lifecycle hooks and Vuex `mapGetters` in production code, `moment` imports, CodeMirror 5.52.2, a hand-bundled Bootstrap-4-beta + jQuery copy under `django_airavata/static/bootstrap-4.0.0-beta/`, `pytz`, and seven workspaces each carrying their own near-duplicate Vite / ESLint / Prettier configs.

This umbrella coordinates the cleanup into five independent tracks. Each lands on a feature branch, merges into a long-lived `modernization` branch, and the whole branch merges to main only when every track is green.

## Goals

- Replace accumulated legacy idioms with current best-in-class equivalents so future feature work hits a modern baseline.
- Establish a real automated-test safety net (Vitest component tests + Playwright E2E) before the large-blast-radius Vue rewrite.
- Preserve functional parity end-to-end. Modernization is invisible to end users; every screen still renders, every action still works. Bug fixes that fall out naturally are allowed but called out in commit messages.
- Leave the codebase consistently styled so future contributors learn one lint/format baseline, one Vite config template, one test harness shape — not seven variants.

## Non-goals

- Redesigning features or information architecture. Confusing screens stay confusing (separate work).
- Rewriting the Python SDK or the airavata server.
- Migrating the database engine. WAL mode covered the known dev-env pain.
- Switching JS framework. Vue 3 stays.
- Adding production deployment changes (Docker, k8s, reverse proxy).
- 100% unit-test coverage. Tests target the ~25 critical components and ~12 user journeys, not exhaustive coverage.
- Internationalization, accessibility overhaul, or performance rewrite — any of these could be their own umbrella.

## Cross-track guardrails

These decisions are locked here so per-track brainstorms don't relitigate them.

**Testing before Track A is a gate, not a guideline.** Track A cannot start until Pre-A ships with green CI on both the Vitest and Playwright harnesses.

**TypeScript in Track A.** Every `.vue` migrated becomes `<script setup lang="ts">`. Standalone `.js` files become `.ts` when they define types/models (models, stores, typed services); pure-glue entry files can stay `.js` only if converting adds no value. `tsconfig.base.json` has `"strict": true` on from day one. The Pre-A test harness is authored in TS from day one.

**Functional parity.** No behavioural changes during modernization. Tempting side-quests ("while we're here we could refactor X") get deferred to a follow-up. Exception: bug fixes that fall out naturally are allowed, logged in commit messages.

**Browser support.** Match the current `browserslist` (`> 1%, last 2 versions, not dead`). CodeMirror 6 and SharedWorker both hit this baseline. Tightening can follow in a later cleanup after parity is verified.

**Python floor.** Stay on 3.12. Bumping to 3.13 is a separate decision outside this umbrella.

**Package manager.** Keep Yarn 1 classic. Corepack pin gives reproducible installs. A pnpm or Yarn 4 switch is its own future track if desired.

**Rollback.** Every track lands on its own feature branch → PR → merge to a long-lived `modernization` branch, which merges to main only at the end. Any track can be reverted independently.

## Tracks and sequencing

Sequence: **D → C → (B ∥ Pre-A) → A**.

### Track D — Python hygiene

Smallest and fully independent. Can start immediately.

- Swap `pytz` for stdlib `zoneinfo` across all call sites.
- Investigate and resolve `setuptools<81` pin — identify what requires it, upgrade or document.
- Audit remaining deps for stale pins (`logging-formatter-anticrlf`, the `codemirror` / `vue-slider-component` pins via their Python-side siblings if any) — either bump or comment rationale in `pyproject.toml`.
- Delete any dead Python modules surfaced by the audit.

**Ships:** clean `pyproject.toml` with no unexplained version-range workarounds; zero calls to deprecated Python stdlib or `pytz` APIs.

**Depends on:** nothing.

**Rough size:** 1 day.

### Track C — Monorepo tooling

Foundation for every JS track. Lands before Track B / Pre-A / A start.

- Lift shared Vite / ESLint / Prettier configs into a root `tooling/` workspace; the 7 app workspaces extend from there.
- Upgrade ESLint 8 → 9 (flat config).
- Configure `vue-tsc` + `tsconfig.base.json` in the root so Track A can land TypeScript cleanly.
- Pin Node via `corepack` + add `packageManager` field to root `package.json`.
- Add root `yarn lint` / `yarn format` / `yarn typecheck` / `yarn test` / `yarn test:e2e` that call into every workspace.

**Ships:** one Vite config template, one ESLint flat config, one Prettier config, one `tsconfig.base.json`, all extended by the 7 workspaces; Node pinned via corepack.

**Depends on:** Track D merged (avoids concurrent `pyproject.toml` churn when someone rebases).

**Rough size:** 2-3 days.

### Track B — JS library swaps

Runs in parallel with Track Pre-A. Both gate Track A.

- `moment` → `date-fns` across the 9 current import sites. `date-fns` chosen over `dayjs` for tree-shaking and closer alignment with `Intl` semantics.
- CodeMirror 5.52.2 → CodeMirror 6. Wrap in a single `<CodeEditor>` Vue component so the API shift is confined; the 3 consuming `.vue` files (`MultiFileInputEditor`, `FileInputEditor`, `UserStorageTextEditViewer`) swap to the wrapper.
- Delete `django_airavata/static/bootstrap-4.0.0-beta/` after grep-proving nothing references it (Django templates, Python, JS, CSS).
- Upgrade `vue-slider-component` off `4.1.0-beta.7` or replace with a maintained alternative.
- Remove `lodash` in the 2 remaining call sites using native ES2020 equivalents.

**Ships:** one fewer deprecated dep, one fewer pre-release dep, one deleted fossil, a reusable `<CodeEditor>` Vue component.

**Depends on:** Track C.

**Rough size:** 3-5 days.

### Track Pre-A — Test harness

Runs in parallel with Track B. Together they gate Track A.

- **Vitest + `@vue/test-utils`** covering ~25 critical components: workspace experiment editor, experiment list, project list, app deployment editor, user storage viewer, IAM user management panel, auth login flow components, etc.
- **Playwright** E2E for ~12 user journeys: login, project create, app launch wizard, file upload, experiment launch, admin users page, notices manager, logout, unauth landing page, CMS page, SSH key management, gateway settings.
- Wire both into CI via root `yarn test` (Vitest) and `yarn test:e2e` (Playwright).
- 1-page contributor doc covering "how to add a new component test" and "how to add a new Playwright journey".

**Ships:** green CI job running both harnesses; test files committed; contributor doc.

**Depends on:** Track C.

**Rough size:** 3-5 days.

### Track A — Vue Options API → Composition API + TypeScript + Pinia

Biggest and riskiest. Blocked until Track B and Track Pre-A have both merged to `modernization`.

- Add `vue-tsc`, `@vue/language-server`, and `typescript` to root tooling (groundwork from Track C).
- Migrate 178 `.vue` files to `<script setup lang="ts">`; delete residual `this.$set`, `this.$off`, `destroyed()`, `beforeDestroy()`, `mapGetters` / `mapMutations` / `mapActions`.
- Migrate Vuex 4 stores → Pinia (~8 store files across `auth/`, `workspace/`, `common/`).
- Convert `.js` files to `.ts` where they define types/models; pure-glue entry files can stay `.js` if conversion adds no value.
- Enable strict TS (`"strict": true`); a follow-up cleanup pass (inside Track A) removes any `@ts-expect-error` tactical relief added during the rewrite.

**Ships:**

```
grep -rn "destroyed\s*(\|beforeDestroy\s*(\|\$set(\|\$off(\|mapGetters\|mapMutations\|mapActions\|from [\"']moment[\"']\|codemirror[/\"']5" \
  django_airavata --include='*.vue' --include='*.js' --include='*.ts'
```

returns **zero** matches. `vue-tsc --noEmit` passes with strict. `yarn test` and `yarn test:e2e` remain green throughout.

**Depends on:** Track C, Track B, and Track Pre-A all merged to `modernization`.

**Rough size:** 2-3 weeks (realistic).

## Done criteria for the umbrella

- All five tracks merged to `main`.
- `grep -rn "destroyed\s*(\|beforeDestroy\s*(\|\$set(\|\$off(\|mapGetters\|mapMutations\|mapActions\|from [\"']moment[\"']\|codemirror[/\"']5" django_airavata` returns zero.
- `django_airavata/static/bootstrap-4.0.0-beta/` does not exist; no checked-in vendored JS libraries remain.
- `vue-tsc --noEmit` passes with `"strict": true`.
- `yarn test` (Vitest) and `yarn test:e2e` (Playwright) run green in CI.
- `ruff check .` and `ty check .` both clean on the Python side.
- `grep -rn "pytz" django_airavata --include='*.py'` returns zero.
- `pyproject.toml` contains no `<` version pins except where a pin has a rationale comment.
- The ~12 Playwright journeys and ~25 Vitest component suites still exercise the same user-visible paths they did on day 1 of Pre-A (no silent test decay).

## Risks and mitigations

| Risk | Mitigation |
|---|---|
| Vue Options → Composition rewrite regressing a screen nobody tests | Pre-A gate: Playwright covers top journeys, Vitest covers top components; Track A blocked until green |
| CodeMirror 6 API rewrite breaking file editor / input editors | Wrap in one `<CodeEditor>` Vue component so the rewrite is confined; Pre-A has a Vitest spec pinning the component's public API |
| ESLint 9 flat config churn breaking in-flight Track A PRs | Track C lands entirely before Track A starts (sequencing enforces) |
| Track A becoming a permanently-open PR | File-by-file or app-by-app commits inside Track A's long-lived branch; integrate to `modernization` weekly; branch has full CI |
| TypeScript strict catching pre-existing latent bugs | Convert file-by-file with per-file `@ts-expect-error` as tactical relief; follow-up cleanup pass removes them |
| Bundled Bootstrap 4 fossil deletion turning out to be referenced | Track B's spec greps across the entire repo before `rm -rf`; Playwright covers anything user-facing |
| Pinia migration clashing with existing Vuex store tests | Pre-A store tests target behaviour (actions/selectors), not Vuex API; Track A swaps impl with tests unchanged |
| `setuptools<81` pin turning out to guard a real compat issue | Track D's spec starts by identifying what required the pin (git blame + reading the dep closer); if valid, document and keep |

## Per-track handoff notes (for future brainstorms)

Each track's own brainstorm will design the architecture. Here's the context it inherits from this umbrella.

- **Track D** receives: scope (pytz, setuptools pin, stale-pin audit) + the parity constraint. Must output file-by-file swap list + a pin-audit result.
- **Track C** receives: "lift shared Vite / ESLint / Prettier / TS config to `tooling/`" + `vue-tsc` must compile with strict. Must design the `tooling/` package layout, the flat ESLint config shape, and how the 7 workspaces extend from it.
- **Track B** receives: specific swap list (`moment`, CodeMirror, Bootstrap-4 fossil, `vue-slider-component`, `lodash`). Must design the `<CodeEditor>` Vue component's public API, migration path for the 3 consuming `.vue` files, and the fossil-deletion verification procedure.
- **Track Pre-A** receives: list of ~25 critical components for Vitest and ~12 journeys for Playwright. Must design shared test utilities (auth helpers, API mocks, Playwright fixtures), CI job layout, and contributor docs.
- **Track A** receives: parity constraint + TS strict + Pre-A as gate + Pinia scope. Must design rewrite order (by app? by route? by dependency depth?), Pinia store layout, commit cadence inside the long-lived branch, and how per-file TS escape hatches are tracked and resolved.

## Next step

**Do not** move directly to implementation. The next action is to brainstorm Track D (smallest, independent) using the brainstorming skill → writing-plans skill → implementation. Subsequent tracks follow in sequence; Track B and Pre-A can be brainstormed in parallel once Track C ships.
