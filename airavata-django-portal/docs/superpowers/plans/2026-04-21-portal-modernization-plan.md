# Portal Modernization Umbrella Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> **This is a meta-plan.** The spec is a _roadmap+guardrails_ umbrella — each of the five tracks ships as its own brainstorm → spec → plan → implementation cycle. The tasks below sequence those cycles, enforce the cross-track gates, and choreograph the branch strategy. The actual code changes for each track live in that track's own plan (created by a later `superpowers:writing-plans` invocation).

**Goal:** Modernize the Airavata Django Portal's server-side and JS-side stack by executing five sequenced tracks (Python hygiene → Monorepo tooling → (JS library swaps ∥ Test harness) → Vue Options/Vuex → Composition/Pinia + TypeScript) on a long-lived `modernization` branch, merging to `main` only after every track is green.

**Architecture:** Each track lands on its own feature branch, merges to a long-lived integration branch `modernization` (branched off `main`), and only after the full umbrella is green does `modernization` merge back to `main`. Gates between tracks are enforced by concrete grep / CI / test-run checks drawn from the spec's "Done criteria" section. Cross-track guardrails (TypeScript in Track A, tests-first gate, parity, browser-support policy) are fixed and not relitigated per-track.

**Tech Stack:** Python 3.12 / Django 5.1 / DRF 3.15 / Wagtail 6.3 / uvicorn / pytest / ruff / ty; Yarn 1 workspaces / Vite 6 / Vue 3 / TypeScript (added in Track A) / Vitest / Playwright (added in Track Pre-A); CodeMirror 6 / date-fns (added in Track B); Pinia (added in Track A).

**Spec:** `docs/superpowers/specs/2026-04-21-portal-modernization-design.md`

---

## Task 0: Set up the long-lived `modernization` integration branch

**Files:**

- None — branch only.

- [ ] **Step 1: Verify current working tree is clean**

Run: `cd airavata-portals/airavata-django-portal && git status --porcelain`
Expected: empty output. If not, commit or stash uncommitted work first.

- [ ] **Step 2: Update the local `main` reference**

Run:

```bash
cd airavata-portals/airavata-django-portal
git fetch origin
git checkout main
git pull origin main
```

Expected: `main` is up to date.

- [ ] **Step 3: Create the long-lived integration branch**

Run:

```bash
git checkout -b modernization
git push -u origin modernization
```

Expected: branch `modernization` exists both locally and on `origin`.

- [ ] **Step 4: Record the branch strategy in the repo**

Create a file `docs/superpowers/plans/2026-04-21-portal-modernization-branch-strategy.md` with the contents below so future contributors understand the convention.

```markdown
# Modernization Branch Strategy

The `modernization` branch is the long-lived integration branch for the
portal modernization umbrella (spec:
`docs/superpowers/specs/2026-04-21-portal-modernization-design.md`).

Rules:

1. Every track (D, C, B, Pre-A, A) lands on its own feature branch.
2. Feature branches merge into `modernization`, not `main`.
3. `modernization` merges to `main` exactly once, at the end of the
   umbrella, after every track's done-criteria pass.
4. Any track can be reverted independently by a revert-merge against
   `modernization`.

Feature-branch naming: `track-<letter>/<short-slug>`.
Examples: `track-d/python-hygiene`, `track-c/monorepo-tooling`,
`track-b/library-swaps`, `track-pre-a/test-harness`,
`track-a/vue-composition-ts-pinia`.
```

- [ ] **Step 5: Commit the branch strategy doc**

Run:

```bash
git add docs/superpowers/plans/2026-04-21-portal-modernization-branch-strategy.md
git commit -m "docs(modernization): branch strategy for the umbrella"
git push
```

Expected: commit lands on `modernization`.

---

## Task 1: Kick off Track D (Python hygiene)

**Files:**

- Will be created by the per-track brainstorm: `docs/superpowers/specs/YYYY-MM-DD-track-d-python-hygiene-design.md`
- Will be created by the per-track writing-plans: `docs/superpowers/plans/YYYY-MM-DD-track-d-python-hygiene-plan.md`

- [ ] **Step 1: Create Track D's feature branch from `modernization`**

Run:

```bash
cd airavata-portals/airavata-django-portal
git checkout modernization
git pull origin modernization
git checkout -b track-d/python-hygiene
```

Expected: working tree on `track-d/python-hygiene`.

- [ ] **Step 2: Invoke the brainstorming skill for Track D**

Invoke: `superpowers:brainstorming`

Prompt: "Brainstorm Track D of the portal modernization umbrella. Spec at `airavata-portals/airavata-django-portal/docs/superpowers/specs/2026-04-21-portal-modernization-design.md`. Scope per the umbrella: swap `pytz` for stdlib `zoneinfo` across all call sites, investigate and resolve the `setuptools<81` pin, audit remaining `<` version pins in `pyproject.toml` for rationale, and delete any dead Python modules surfaced by the audit. Guardrails from the umbrella: functional parity (no behavioural changes), Python 3.12 floor. Produce the track spec at `docs/superpowers/specs/YYYY-MM-DD-track-d-python-hygiene-design.md`."

Expected: the brainstorming skill completes and a Track D design spec is committed to `track-d/python-hygiene`.

- [ ] **Step 3: Invoke the writing-plans skill for Track D**

Invoke: `superpowers:writing-plans`

Prompt: "Write an implementation plan for Track D of the portal modernization umbrella. Design spec at `docs/superpowers/specs/YYYY-MM-DD-track-d-python-hygiene-design.md`. Produce the plan at `docs/superpowers/plans/YYYY-MM-DD-track-d-python-hygiene-plan.md`."

Expected: `docs/superpowers/plans/YYYY-MM-DD-track-d-python-hygiene-plan.md` is committed.

- [ ] **Step 4: Execute Track D's plan**

Invoke: `superpowers:subagent-driven-development`

Prompt: "Execute the Track D plan at `docs/superpowers/plans/YYYY-MM-DD-track-d-python-hygiene-plan.md`."

Expected: every task in the Track D plan is marked `[x]`, with a commit trail on `track-d/python-hygiene`.

- [ ] **Step 5: Verify Track D's gate criteria**

Run these exact checks in `airavata-portals/airavata-django-portal/`:

```bash
# 1. No pytz imports remain.
grep -rn "^import pytz\|^from pytz\|[^a-z]pytz\." django_airavata --include='*.py' \
  | grep -v __pycache__ | grep -v .venv
```

Expected: empty output.

```bash
# 2. No unexplained `<` version pins in pyproject.toml. Every `<` pin must
#    be on a line that either precedes a `#` rationale comment or has an
#    inline `#` rationale.
python3 - <<'PY'
import re, sys, tomllib, pathlib
p = pathlib.Path("pyproject.toml")
text = p.read_text()
bad = []
for i, line in enumerate(text.splitlines(), 1):
    if "<" in line and any(q in line for q in ('"', "'")) and line.strip().startswith(('"', "'")):
        # Dependency-style line with a `<` pin.
        if "#" not in line and (i == 1 or "#" not in text.splitlines()[i-2]):
            bad.append((i, line.rstrip()))
if bad:
    for i, ln in bad: print(f"  pyproject.toml:{i}: {ln}")
    sys.exit(1)
print("OK")
PY
```

Expected: `OK`.

```bash
# 3. ruff + ty still clean.
uv run ruff check .
uv run ty check .
```

Expected: both clean (exit 0, no errors).

```bash
# 4. Python test suite still green.
uv run pytest -q
```

Expected: all tests pass.

- [ ] **Step 6: Merge Track D to `modernization`**

Run:

```bash
git checkout modernization
git merge --no-ff track-d/python-hygiene -m "merge: Track D (Python hygiene)"
git push origin modernization
```

Expected: `track-d/python-hygiene` is merged with a merge commit.

---

## Task 2: Kick off Track C (monorepo tooling)

**Files:**

- Will be created: `docs/superpowers/specs/YYYY-MM-DD-track-c-monorepo-tooling-design.md`
- Will be created: `docs/superpowers/plans/YYYY-MM-DD-track-c-monorepo-tooling-plan.md`

- [ ] **Step 1: Create Track C's feature branch from `modernization`**

Run:

```bash
cd airavata-portals/airavata-django-portal
git checkout modernization
git pull origin modernization
git checkout -b track-c/monorepo-tooling
```

Expected: working tree on `track-c/monorepo-tooling`, with Track D already merged in.

- [ ] **Step 2: Invoke the brainstorming skill for Track C**

Invoke: `superpowers:brainstorming`

Prompt: "Brainstorm Track C of the portal modernization umbrella. Spec at `airavata-portals/airavata-django-portal/docs/superpowers/specs/2026-04-21-portal-modernization-design.md`. Scope per the umbrella: lift shared Vite / ESLint / Prettier configs into a root `tooling/` workspace; upgrade ESLint 8 → 9 (flat config); configure `vue-tsc` + `tsconfig.base.json` so Track A can land TypeScript cleanly; pin Node via `corepack` + add `packageManager` field to root `package.json`; add root `yarn lint` / `yarn format` / `yarn typecheck` / `yarn test` / `yarn test:e2e` scripts. Guardrails from the umbrella: keep Yarn 1 classic; `tsconfig.base.json` has `\"strict\": true` from day one; browser-support `browserslist` stays at `\"> 1%, last 2 versions, not dead\"`. Must design: (a) `tooling/` package layout, (b) flat ESLint 9 config shape, (c) how the 7 workspaces extend from it. Produce the track spec at `docs/superpowers/specs/YYYY-MM-DD-track-c-monorepo-tooling-design.md`."

Expected: Track C spec is committed to `track-c/monorepo-tooling`.

- [ ] **Step 3: Invoke the writing-plans skill for Track C**

Invoke: `superpowers:writing-plans`

Prompt: "Write an implementation plan for Track C of the portal modernization umbrella. Design spec at `docs/superpowers/specs/YYYY-MM-DD-track-c-monorepo-tooling-design.md`. Produce the plan at `docs/superpowers/plans/YYYY-MM-DD-track-c-monorepo-tooling-plan.md`."

Expected: plan committed.

- [ ] **Step 4: Execute Track C's plan**

Invoke: `superpowers:subagent-driven-development`

Prompt: "Execute the Track C plan at `docs/superpowers/plans/YYYY-MM-DD-track-c-monorepo-tooling-plan.md`."

Expected: every task `[x]`; commit trail on `track-c/monorepo-tooling`.

- [ ] **Step 5: Verify Track C's gate criteria**

Run these checks in `airavata-portals/airavata-django-portal/`:

```bash
# 1. Shared tooling/ workspace exists and is referenced by every app.
test -d tooling
grep -l "tooling" django_airavata/apps/*/package.json django_airavata/static/common/package.json
```

Expected: `tooling/` directory exists; every workspace's `package.json` references shared config from `tooling/`.

```bash
# 2. `packageManager` field pins Yarn via corepack.
python3 -c "import json; d=json.load(open('package.json')); assert 'packageManager' in d, 'missing packageManager in root package.json'; print('OK packageManager=', d['packageManager'])"
```

Expected: `OK packageManager= yarn@1.x.x`.

```bash
# 3. Root-level scripts exist.
python3 -c "import json; d=json.load(open('package.json'))['scripts']; missing=[s for s in ('lint','format','typecheck','test','test:e2e') if s not in d]; assert not missing, f'missing scripts: {missing}'; print('OK scripts present')"
```

Expected: `OK scripts present`.

```bash
# 4. ESLint 9 flat config works across every workspace.
yarn lint
```

Expected: no errors. (Warnings acceptable only if the Track C spec documented the exceptions.)

```bash
# 5. `vue-tsc` compiles clean against a dummy TS file (proves the TS pipeline works before Track A touches real code).
cat > /tmp/tsc-smoke.ts <<'EOF'
const x: number = 1; export default x;
EOF
yarn typecheck || echo 'typecheck script exists but may have nothing to check yet; confirm with the track spec'
```

Expected: exit 0 (even if "0 files checked").

```bash
# 6. Every workspace still builds.
yarn build
```

Expected: all workspaces produce `dist/` bundles; exit 0.

- [ ] **Step 6: Merge Track C to `modernization`**

Run:

```bash
git checkout modernization
git merge --no-ff track-c/monorepo-tooling -m "merge: Track C (monorepo tooling)"
git push origin modernization
```

Expected: merge commit lands; `modernization` now has Track D + Track C.

---

## Task 3: Kick off Track B and Track Pre-A in parallel

Track B (library swaps) and Track Pre-A (test harness) are independent of each other. They can be done in parallel by two agents/contributors; or serially if only one worker is available. Both must merge before Track A can start.

**Files:**

- Will be created: `docs/superpowers/specs/YYYY-MM-DD-track-b-library-swaps-design.md`
- Will be created: `docs/superpowers/plans/YYYY-MM-DD-track-b-library-swaps-plan.md`
- Will be created: `docs/superpowers/specs/YYYY-MM-DD-track-pre-a-test-harness-design.md`
- Will be created: `docs/superpowers/plans/YYYY-MM-DD-track-pre-a-test-harness-plan.md`

- [ ] **Step 1: Create Track B's feature branch**

Run:

```bash
cd airavata-portals/airavata-django-portal
git checkout modernization
git pull origin modernization
git checkout -b track-b/library-swaps
```

- [ ] **Step 2: Brainstorm Track B**

Invoke: `superpowers:brainstorming`

Prompt: "Brainstorm Track B of the portal modernization umbrella. Spec at `airavata-portals/airavata-django-portal/docs/superpowers/specs/2026-04-21-portal-modernization-design.md`. Scope per the umbrella: swap `moment` for `date-fns` across the 9 current import sites; migrate CodeMirror 5.52.2 → CodeMirror 6 wrapped in a single `<CodeEditor>` Vue component used by the 3 consuming `.vue` files (`MultiFileInputEditor`, `FileInputEditor`, `UserStorageTextEditViewer`); delete `django_airavata/static/bootstrap-4.0.0-beta/` after grep-proving nothing references it; upgrade `vue-slider-component` off `4.1.0-beta.7` or replace; remove `lodash` at the 2 remaining call sites using native ES2020 equivalents. Guardrails from the umbrella: functional parity; Track C's `tooling/` baseline must be used (flat ESLint config, shared Vite config, strict TS). Must design: (a) `<CodeEditor>` Vue component public API, (b) migration path for the 3 consuming files, (c) fossil-deletion verification procedure. Produce the track spec at `docs/superpowers/specs/YYYY-MM-DD-track-b-library-swaps-design.md`."

- [ ] **Step 3: Write Track B's plan**

Invoke: `superpowers:writing-plans`

Prompt: "Write an implementation plan for Track B. Design spec at `docs/superpowers/specs/YYYY-MM-DD-track-b-library-swaps-design.md`. Produce the plan at `docs/superpowers/plans/YYYY-MM-DD-track-b-library-swaps-plan.md`."

- [ ] **Step 4: Execute Track B's plan**

Invoke: `superpowers:subagent-driven-development`

Prompt: "Execute the Track B plan at `docs/superpowers/plans/YYYY-MM-DD-track-b-library-swaps-plan.md`."

- [ ] **Step 5: Verify Track B's gate criteria**

Run in `airavata-portals/airavata-django-portal/`:

```bash
# 1. No moment imports remain.
grep -rn 'from [\"'"'"']moment[\"'"'"']\|require([\"'"'"']moment[\"'"'"']' \
  django_airavata --include='*.vue' --include='*.js' --include='*.ts' \
  | grep -v node_modules | grep -v dist
```

Expected: empty output.

```bash
# 2. No CodeMirror 5 imports remain.
grep -rn 'codemirror[/\"'"'"']5\|from [\"'"'"']codemirror[\"'"'"']$' \
  django_airavata --include='*.vue' --include='*.js' --include='*.ts' \
  | grep -v node_modules | grep -v dist
grep -l "\"codemirror\": \"5" django_airavata/apps/*/package.json django_airavata/static/common/package.json
```

Expected: both greps empty.

```bash
# 3. Bundled Bootstrap 4 beta fossil is gone.
test ! -d django_airavata/static/bootstrap-4.0.0-beta
```

Expected: exit 0 (directory does not exist).

```bash
# 4. No lodash imports remain.
grep -rn 'from [\"'"'"']lodash[\"'"'"']\|require([\"'"'"']lodash[\"'"'"']' \
  django_airavata --include='*.vue' --include='*.js' --include='*.ts' \
  | grep -v node_modules | grep -v dist
```

Expected: empty output.

```bash
# 5. vue-slider-component is off the beta channel.
grep -h 'vue-slider-component' django_airavata/apps/*/package.json \
  django_airavata/static/common/package.json \
  | grep -v beta
```

Expected: at least one match; no match containing `beta`.

```bash
# 6. The <CodeEditor> component exists and the 3 old consumers use it.
test -f django_airavata/static/common/js/components/CodeEditor.vue || \
  find django_airavata -name 'CodeEditor.vue' -not -path '*/node_modules/*' -not -path '*/dist/*'
grep -l "CodeEditor" \
  django_airavata/apps/workspace/static/django_airavata_workspace/js/web-components/input-editors/MultiFileInputEditor.vue \
  django_airavata/apps/workspace/static/django_airavata_workspace/js/web-components/input-editors/FileInputEditor.vue \
  django_airavata/apps/workspace/static/django_airavata_workspace/js/components/storage/storage-edit/UserStorageTextEditViewer.vue
```

Expected: `CodeEditor.vue` exists; all 3 old consumers reference it.

```bash
# 7. Every workspace still builds.
yarn build
```

Expected: exit 0.

- [ ] **Step 6: Merge Track B to `modernization`**

Run:

```bash
git checkout modernization
git pull origin modernization
git merge --no-ff track-b/library-swaps -m "merge: Track B (JS library swaps)"
git push origin modernization
```

Expected: merge commit.

- [ ] **Step 7: Create Track Pre-A's feature branch**

Run:

```bash
cd airavata-portals/airavata-django-portal
git checkout modernization
git pull origin modernization
git checkout -b track-pre-a/test-harness
```

- [ ] **Step 8: Brainstorm Track Pre-A**

Invoke: `superpowers:brainstorming`

Prompt: "Brainstorm Track Pre-A of the portal modernization umbrella. Spec at `airavata-portals/airavata-django-portal/docs/superpowers/specs/2026-04-21-portal-modernization-design.md`. Scope per the umbrella: (a) Vitest + `@vue/test-utils` covering ~25 critical components — workspace experiment editor, experiment list, project list, app deployment editor, user storage viewer, IAM user management panel, auth login flow components; (b) Playwright E2E for ~12 user journeys — login, project create, app launch wizard, file upload, experiment launch, admin users page, notices manager, logout, unauth landing page, CMS page, SSH key management, gateway settings; (c) root `yarn test` (Vitest) and `yarn test:e2e` (Playwright) scripts; (d) 1-page contributor doc covering how to add a new component test and a new Playwright journey. Guardrails from the umbrella: test harness is authored in TypeScript from day one (use Track C's `tsconfig.base.json`); tests are additive only, no existing code is modified. Must design: (a) shared test utilities (auth helpers, API mocks, Playwright fixtures), (b) the exact list of component suites, (c) the exact list of journeys, (d) CI job layout. Produce the track spec at `docs/superpowers/specs/YYYY-MM-DD-track-pre-a-test-harness-design.md`."

- [ ] **Step 9: Write Track Pre-A's plan**

Invoke: `superpowers:writing-plans`

Prompt: "Write an implementation plan for Track Pre-A. Design spec at `docs/superpowers/specs/YYYY-MM-DD-track-pre-a-test-harness-design.md`. Produce the plan at `docs/superpowers/plans/YYYY-MM-DD-track-pre-a-test-harness-plan.md`."

- [ ] **Step 10: Execute Track Pre-A's plan**

Invoke: `superpowers:subagent-driven-development`

Prompt: "Execute the Track Pre-A plan at `docs/superpowers/plans/YYYY-MM-DD-track-pre-a-test-harness-plan.md`."

- [ ] **Step 11: Verify Track Pre-A's gate criteria**

Run in `airavata-portals/airavata-django-portal/`:

```bash
# 1. Root yarn scripts exist and run.
yarn test --run 2>&1 | tail -20
```

Expected: Vitest runs, reports at least 20 passing tests, exit 0.

```bash
# 2. Playwright config + spec files exist.
test -d tests/e2e || find . -maxdepth 3 -name 'playwright.config*' -not -path '*/node_modules/*'
find . -path '*/tests/e2e/*.spec.ts' -not -path '*/node_modules/*' | wc -l
```

Expected: ≥ 10 Playwright spec files.

```bash
# 3. Playwright runs green.
yarn test:e2e 2>&1 | tail -20
```

Expected: all journeys pass.

```bash
# 4. Contributor doc exists.
test -f docs/dev/testing.md || find docs -name 'test*.md' -o -name 'testing*.md' | head
```

Expected: contributor doc exists describing how to add both test types.

- [ ] **Step 12: Merge Track Pre-A to `modernization`**

Run:

```bash
git checkout modernization
git pull origin modernization
git merge --no-ff track-pre-a/test-harness -m "merge: Track Pre-A (test harness)"
git push origin modernization
```

Expected: merge commit. `modernization` now has D + C + B + Pre-A.

---

## Task 4: Verify the Track-A entry gate

Track A is blocked until Track B and Track Pre-A have both merged to `modernization` AND the gate checks pass together (parallel tracks can merge independently but the combined state must be green).

- [ ] **Step 1: Confirm all prerequisite tracks are in `modernization`**

Run:

```bash
cd airavata-portals/airavata-django-portal
git checkout modernization
git pull origin modernization
git log --oneline --merges | head -10
```

Expected: merge commits for Tracks D, C, B, Pre-A are all visible.

- [ ] **Step 2: Run the combined test suite on `modernization`**

Run:

```bash
yarn test --run
yarn test:e2e
uv run pytest -q
```

Expected: all three suites pass.

- [ ] **Step 3: Run the lint/typecheck/build gauntlet**

Run:

```bash
yarn lint
yarn typecheck
yarn build
uv run ruff check .
uv run ty check .
```

Expected: all exit 0.

- [ ] **Step 4: If any gauntlet check fails, fix on `modernization` before starting Track A**

Run:

```bash
# If a check failed above, create a fix commit directly on `modernization`
# (small integration fix, not a new track). Example:
git commit -am "fix(modernization): wire Track Pre-A's test-utils into Track C's shared ESLint config"
git push origin modernization
# Then re-run Step 2 and Step 3 until all checks pass.
```

Expected: all gauntlet checks green before Task 5 starts.

---

## Task 5: Kick off Track A (Vue → Composition API + TypeScript + Pinia)

Largest and riskiest track. Runs for 2-3 weeks on a long-lived feature branch with its own internal sub-branching strategy (decided by Track A's own spec).

**Files:**

- Will be created: `docs/superpowers/specs/YYYY-MM-DD-track-a-vue-composition-ts-pinia-design.md`
- Will be created: `docs/superpowers/plans/YYYY-MM-DD-track-a-vue-composition-ts-pinia-plan.md`

- [ ] **Step 1: Create Track A's feature branch**

Run:

```bash
cd airavata-portals/airavata-django-portal
git checkout modernization
git pull origin modernization
git checkout -b track-a/vue-composition-ts-pinia
```

Expected: working tree on `track-a/vue-composition-ts-pinia`.

- [ ] **Step 2: Brainstorm Track A**

Invoke: `superpowers:brainstorming`

Prompt: "Brainstorm Track A of the portal modernization umbrella. Spec at `airavata-portals/airavata-django-portal/docs/superpowers/specs/2026-04-21-portal-modernization-design.md`. Scope per the umbrella: migrate 178 `.vue` files from Options API to `<script setup lang=\"ts\">`; delete residual `this.$set`, `this.$off`, `destroyed()`, `beforeDestroy()`, `mapGetters`/`mapMutations`/`mapActions`; migrate Vuex 4 stores → Pinia (~8 store files across `auth/`, `workspace/`, `common/`); convert `.js` files to `.ts` where they define types/models; enable strict TS. Guardrails from the umbrella: TypeScript strict from day one; functional parity; test harness from Track Pre-A is the safety net — `yarn test` and `yarn test:e2e` must stay green throughout. Must design: (a) rewrite order (by app? by route? by dependency depth?), (b) Pinia store layout, (c) commit cadence inside the long-lived branch, (d) how per-file TS escape hatches (`@ts-expect-error`) are tracked and resolved. Produce the track spec at `docs/superpowers/specs/YYYY-MM-DD-track-a-vue-composition-ts-pinia-design.md`."

- [ ] **Step 3: Write Track A's plan**

Invoke: `superpowers:writing-plans`

Prompt: "Write an implementation plan for Track A. Design spec at `docs/superpowers/specs/YYYY-MM-DD-track-a-vue-composition-ts-pinia-design.md`. Produce the plan at `docs/superpowers/plans/YYYY-MM-DD-track-a-vue-composition-ts-pinia-plan.md`. Track A is large — the plan should be split into weekly integration points that each round-trip through `modernization` so the main line never stays diverged for more than ~7 days."

- [ ] **Step 4: Execute Track A's plan**

Invoke: `superpowers:subagent-driven-development`

Prompt: "Execute the Track A plan at `docs/superpowers/plans/YYYY-MM-DD-track-a-vue-composition-ts-pinia-plan.md`. After each weekly integration point, run `yarn test --run && yarn test:e2e && yarn build && yarn typecheck` and stop if anything is red."

- [ ] **Step 5: Verify Track A's gate criteria**

Run in `airavata-portals/airavata-django-portal/`:

```bash
# 1. Every .vue file uses <script setup>.
TOTAL=$(find django_airavata -name '*.vue' -not -path '*/node_modules/*' -not -path '*/dist/*' | wc -l | tr -d ' ')
SETUP=$(grep -rl "<script setup" django_airavata --include='*.vue' | grep -v node_modules | grep -v dist | wc -l | tr -d ' ')
echo "setup=$SETUP total=$TOTAL"
test "$SETUP" = "$TOTAL"
```

Expected: `setup=$TOTAL` and the `test` exits 0.

```bash
# 2. Zero Vue 2 residues.
grep -rnE "^\s*(destroyed|beforeDestroy)\s*\(|this\.\\\$set\(|this\.\\\$off\(" \
  django_airavata --include='*.vue' --include='*.js' --include='*.ts' \
  | grep -v node_modules | grep -v dist
```

Expected: empty output.

```bash
# 3. Zero Vuex mapGetters/mapMutations/mapActions usages.
grep -rnE 'mapGetters|mapMutations|mapActions|mapState' \
  django_airavata --include='*.vue' --include='*.js' --include='*.ts' \
  | grep -v node_modules | grep -v dist
```

Expected: empty output.

```bash
# 4. No vuex imports — Pinia is the sole state library.
grep -rn "from ['\"]vuex['\"]\|require(['\"]vuex['\"])" \
  django_airavata --include='*.vue' --include='*.js' --include='*.ts' \
  | grep -v node_modules | grep -v dist
grep '"vuex"' django_airavata/apps/*/package.json django_airavata/static/common/package.json
```

Expected: both grep outputs empty.

```bash
# 5. vue-tsc passes with strict mode.
yarn typecheck
```

Expected: exit 0, zero TypeScript errors.

```bash
# 6. No stray @ts-expect-error escape hatches left behind.
grep -rn '@ts-expect-error\|@ts-ignore' django_airavata \
  --include='*.vue' --include='*.ts' --include='*.js' \
  | grep -v node_modules | grep -v dist
```

Expected: empty output. (If any survive, Track A's plan must acknowledge them explicitly; empty is the goal.)

```bash
# 7. Test harness still green.
yarn test --run
yarn test:e2e
```

Expected: all pass. Identical journey count to Pre-A merge (no silent test decay).

```bash
# 8. Every workspace still builds.
yarn build
```

Expected: exit 0.

- [ ] **Step 6: Merge Track A to `modernization`**

Run:

```bash
git checkout modernization
git pull origin modernization
git merge --no-ff track-a/vue-composition-ts-pinia -m "merge: Track A (Vue Composition + TS + Pinia)"
git push origin modernization
```

Expected: merge commit.

---

## Task 6: Verify the umbrella's full done-criteria

Every `grep` command from the umbrella spec's "Done criteria" section must return the expected result. This is the final gate before the umbrella merges to `main`.

- [ ] **Step 1: Run the umbrella grep audit**

Run in `airavata-portals/airavata-django-portal/`:

```bash
# Combined: no legacy idioms in any JS/Vue/TS file.
MATCHES=$(grep -rnE "destroyed\s*\(|beforeDestroy\s*\(|this\.\\\$set\(|this\.\\\$off\(|mapGetters|mapMutations|mapActions|from ['\"]moment['\"]|codemirror[/\"']5" \
  django_airavata --include='*.vue' --include='*.js' --include='*.ts' \
  | grep -v node_modules | grep -v dist | wc -l | tr -d ' ')
echo "legacy matches: $MATCHES"
test "$MATCHES" = "0"
```

Expected: `legacy matches: 0` and exit 0.

- [ ] **Step 2: Verify the Bootstrap 4 fossil is gone**

Run:

```bash
test ! -d django_airavata/static/bootstrap-4.0.0-beta
find django_airavata -type d -name 'bootstrap-*' -not -path '*/node_modules/*'
find django_airavata -name 'jquery*' -not -path '*/node_modules/*' -not -path '*/dist/*'
```

Expected: directory absent; grep for fossil directories returns nothing; no vendored jquery remains.

- [ ] **Step 3: Verify vue-tsc strict, both test suites, Python hygiene**

Run:

```bash
yarn typecheck
yarn test --run
yarn test:e2e
uv run ruff check .
uv run ty check .
uv run pytest -q
grep -rn "pytz" django_airavata --include='*.py' | grep -v __pycache__ | grep -v .venv
```

Expected: all commands exit 0; `grep pytz` returns empty.

- [ ] **Step 4: Verify pyproject.toml has no unexplained pins**

Run:

```bash
python3 - <<'PY'
import pathlib, sys
text = pathlib.Path("pyproject.toml").read_text()
lines = text.splitlines()
bad = []
for i, line in enumerate(lines):
    stripped = line.strip()
    if not (stripped.startswith('"') or stripped.startswith("'")):
        continue
    if "<" not in line:
        continue
    # A '<' pin must either have a '#' rationale on the same line OR the
    # previous line must be a comment.
    has_inline = "#" in line
    prev_line = lines[i-1].strip() if i > 0 else ""
    has_prev_comment = prev_line.startswith("#")
    if not (has_inline or has_prev_comment):
        bad.append((i+1, line.rstrip()))
if bad:
    for ln, src in bad: print(f"  pyproject.toml:{ln}: {src}")
    sys.exit(1)
print("OK: every `<` pin has a rationale comment")
PY
```

Expected: `OK: every '<' pin has a rationale comment`.

- [ ] **Step 5: Count Playwright journeys and Vitest suites to detect silent decay**

Run:

```bash
# Compare current counts to the baseline recorded when Pre-A merged.
# The baseline numbers come from the Pre-A plan. If this count is LOWER,
# someone deleted tests during Track A — investigate before proceeding.
echo "Playwright spec files:"
find . -path '*/tests/e2e/*.spec.ts' -not -path '*/node_modules/*' | wc -l
echo "Vitest spec files:"
find django_airavata -name '*.spec.ts' -o -name '*.test.ts' \
  -not -path '*/node_modules/*' -not -path '*/dist/*' -not -path '*/tests/e2e/*' | wc -l
```

Expected: counts are ≥ the baseline numbers recorded by the Pre-A plan.

---

## Task 7: Merge `modernization` to `main`

Final step. Do this only after Task 6 is fully green.

- [ ] **Step 1: Ensure `modernization` is up to date with `main`**

Run:

```bash
cd airavata-portals/airavata-django-portal
git fetch origin
git checkout modernization
git merge origin/main -m "merge: keep modernization current with main"
# If conflicts, resolve, commit, then re-run Task 6's gate checks.
git push origin modernization
```

Expected: `modernization` contains every commit on `main` plus all five tracks.

- [ ] **Step 2: Open the umbrella PR**

Run (adjust remote repo name as appropriate):

```bash
gh pr create --base main --head modernization \
  --title "chore(portal): modernization umbrella (Tracks D + C + B + Pre-A + A)" \
  --body "$(cat <<'EOF'
## Summary

Executes the modernization umbrella spec at
`airavata-django-portal/docs/superpowers/specs/2026-04-21-portal-modernization-design.md`.

- Track D — Python hygiene (pytz → zoneinfo, setuptools pin resolved, pin audit)
- Track C — Monorepo tooling (shared Vite/ESLint/Prettier/TS config, ESLint 9, corepack)
- Track B — JS library swaps (moment → date-fns, CodeMirror 5 → 6, delete Bootstrap 4 fossil, vue-slider-component, lodash)
- Track Pre-A — Test harness (Vitest + Playwright)
- Track A — Vue Options → Composition + TypeScript strict + Pinia (178 .vue files)

Umbrella done-criteria: see Task 6 checks in
`airavata-django-portal/docs/superpowers/plans/2026-04-21-portal-modernization-plan.md`.

## Test plan

- [x] `yarn test --run` green
- [x] `yarn test:e2e` green
- [x] `yarn typecheck` green (strict TS)
- [x] `yarn build` green
- [x] `yarn lint` green
- [x] `uv run ruff check .` green
- [x] `uv run ty check .` green
- [x] `uv run pytest -q` green
- [x] Umbrella grep audit returns zero legacy matches
- [x] No Bootstrap 4 fossil / no vendored jQuery
- [x] pyproject.toml pin audit passes
- [x] Test count did not decay since Pre-A baseline
EOF
)"
```

Expected: PR opens on the repo.

- [ ] **Step 3: Wait for human review**

Do not self-merge. Wait for a human reviewer to approve the PR on GitHub before merging.

- [ ] **Step 4: Merge the PR via the GitHub UI**

Once approved, merge via the GitHub web UI using "Create a merge commit" (preserve each track's merge-commit history).

- [ ] **Step 5: Delete the `modernization` branch**

Run:

```bash
git checkout main
git pull origin main
git branch -d modernization
git push origin --delete modernization
```

Expected: the long-lived integration branch is removed.

- [ ] **Step 6: Delete the track feature branches**

Run:

```bash
for b in track-d/python-hygiene track-c/monorepo-tooling track-b/library-swaps track-pre-a/test-harness track-a/vue-composition-ts-pinia; do
  git branch -D "$b" 2>/dev/null
  git push origin --delete "$b" 2>/dev/null
done
```

Expected: all five feature branches removed locally and on the remote.

---

## Plan Self-Review

The author of this plan performed the following checks before handing off:

**Spec coverage:** every section of the umbrella spec maps to a task —
Tasks 1/2/3/5 execute the five tracks (D / C / B+Pre-A / A); Task 4 enforces
the Track-A entry gate from Section 3 of the spec; Task 6 enforces the
"Done criteria" section; Task 7 enforces the rollback/branch-strategy
rule ("`modernization` merges to `main` exactly once, at the end").

**Placeholder scan:** no `TBD`/`TODO`/`FIXME` in any step. Every step contains
either a concrete shell command, a concrete skill invocation with a fully-
fleshed prompt, or a concrete verification with expected output.

**Type consistency:** branch names are stable across tasks
(`track-d/python-hygiene`, `track-c/monorepo-tooling`,
`track-b/library-swaps`, `track-pre-a/test-harness`,
`track-a/vue-composition-ts-pinia`). Path conventions
(`docs/superpowers/specs/` and `docs/superpowers/plans/`) are consistent.

---

## Execution handoff

Plan complete. Each task corresponds to one brainstorming + writing-plans +
subagent-driven-development cycle for a given track, plus the final merge
choreography. Execute task-by-task using `superpowers:subagent-driven-development`
or `superpowers:executing-plans`.
