# Track C — Monorepo Tooling Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Land the `tooling/` workspace, Yarn→npm switch, ESLint 9 strict config, TypeScript pipeline foundation, and root scripts as one squashed commit on `track-c/monorepo-tooling`, with functional-parity in built artefacts.

**Architecture:** 8 tasks producing checkpoint commits that squash to one. Task 1 captures the pre-Track-C baseline (built dist manifests). Tasks 2-6 build the tooling, switch package manager, wire workspaces, fix lint violations, add root scripts. Task 7 runs all 15 gate checks. Task 8 squashes and merges. Each task has a concrete verification so we catch regressions early.

**Tech Stack:** Node 22+ / npm workspaces (new) / ESLint 9 (flat config) / Prettier 3 / Vite 6 / vue-tsc 2 / TypeScript 5 (foundation only; Track A uses it).

**Spec:** `docs/superpowers/specs/2026-04-21-track-c-monorepo-tooling-design.md`

**Working directory for every command:** `airavata-portals/airavata-django-portal`.

**Starting branch:** `track-c/monorepo-tooling` (already created off `modernization`, HEAD at `f5d19f7942 docs(track-c): monorepo tooling design spec`).

---

## File Structure

### New files (in `tooling/`)

- `tooling/package.json` — `@airavata/tooling` workspace metadata + dev deps.
- `tooling/README.md` — how to consume the shared configs.
- `tooling/eslint.config.js` — flat strict config.
- `tooling/prettier.config.js` — shared Prettier rules.
- `tooling/vite.config.js` — exports `defineAppConfig()` helper.
- `tooling/tsconfig.base.json` — strict TS base, `allowJs: false`.

### New files (one per workspace, 7 workspaces × 4 files = 28)

- `<workspace>/eslint.config.js` — re-exports from `@airavata/tooling`.
- `<workspace>/prettier.config.js` — re-exports from `@airavata/tooling`.
- `<workspace>/jsconfig.json` — extends `@airavata/tooling/tsconfig.base.json`.
- `<workspace>/vite.config.js` — REPLACES existing; calls `defineAppConfig()`.

### Modified files

- `package.json` (root) — add `tooling` to `workspaces`, add `packageManager`, rewrite `scripts`, drop root `moment` dep (moved per Track B later — keep for now).
- `Tiltfile` — replace `yarn` invocations with `npm`.
- Each workspace's `package.json` — drop `eslint`, `eslint-plugin-vue`, `prettier`, `vite`, `@vitejs/plugin-vue`, `vite-plugin-vue` dev deps; keep `vitest` (workspace-specific), workspace-specific deps stay.
- `yarn.lock` → deleted. `package-lock.json` → created by `npm install`.

### ESLint violation fixes

Touches all 7 workspaces; scope is large but surgical — fixes target specific rules from the strict preset (no-unused-vars, no-undef, no-unreachable, eqeqeq, vue/* recommended).

---

## Task 1: Capture pre-Track-C baseline

**Files:** none (produces `/tmp/td-c-pre-*-dist/` directories + manifest snapshots).

This task runs on `modernization` (not `track-c/monorepo-tooling`) to capture the build output we're going to parity-check against.

- [ ] **Step 1: Verify current working state is clean**

```bash
cd /Users/yasith/code/artisan/worktree-feat-sdk-and-devenv/airavata-portals/airavata-django-portal
git status --porcelain
git branch --show-current
```
Expected: empty status; branch is `track-c/monorepo-tooling`.

- [ ] **Step 2: Temporarily switch to modernization for baseline**

```bash
git checkout modernization
git pull origin modernization
```
Expected: HEAD is the Track D merge commit.

- [ ] **Step 3: Fresh Yarn install + build all workspaces**

```bash
rm -rf node_modules */node_modules \
       django_airavata/apps/*/node_modules \
       django_airavata/apps/workspace/django-airavata-workspace-plugin-api/node_modules
yarn install 2>&1 | tail -3
yarn workspaces run build 2>&1 | tail -10
```
Expected: all 7 workspaces build without error. Some may print warnings — note but ignore.

- [ ] **Step 4: Snapshot every workspace's dist/**

```bash
rm -rf /tmp/td-c-pre-*
mkdir -p /tmp/td-c-pre-snapshots
cp -r django_airavata/static/common/dist /tmp/td-c-pre-common-dist
for app in admin api auth dataparsers workspace; do
  cp -r "django_airavata/apps/$app/static/django_airavata_$app/dist" \
        "/tmp/td-c-pre-$app-dist"
done
# plugin-api is a library (no django static dir; uses its own dist/)
cp -r django_airavata/apps/workspace/django-airavata-workspace-plugin-api/dist \
      /tmp/td-c-pre-plugin-api-dist 2>/dev/null || echo "plugin-api has no dist/"
ls /tmp/td-c-pre-*-dist 2>/dev/null | head
```
Expected: 5-6 snapshot directories at `/tmp/td-c-pre-*-dist/`, each containing a `manifest.json` (except library ones).

- [ ] **Step 5: Snapshot manifest keys for later parity check**

```bash
for app in admin auth dataparsers workspace; do
  python3 -c "
import json
d = json.load(open('/tmp/td-c-pre-$app-dist/manifest.json'))
keys = sorted(d.keys())
print('$app: ' + str(len(keys)) + ' entries')
open('/tmp/td-c-pre-$app-manifest-keys.txt', 'w').write('\n'.join(keys) + '\n')
"
done
cat /tmp/td-c-pre-workspace-manifest-keys.txt | head
```
Expected: each app reports its entry count. `workspace` should have ~18 entries (biggest).

- [ ] **Step 6: Return to track-c/monorepo-tooling**

```bash
git checkout track-c/monorepo-tooling
git status --porcelain  # clean
```
Expected: back on `track-c/monorepo-tooling`, clean tree.

---

## Task 2: Scaffold the `tooling/` workspace

**Files:**
- Create: `tooling/package.json`
- Create: `tooling/README.md`
- Create: `tooling/tsconfig.base.json`
- Create: `tooling/prettier.config.js`
- Create: `tooling/eslint.config.js`
- Create: `tooling/vite.config.js`

- [ ] **Step 1: Create the tooling directory**

```bash
mkdir -p tooling
```

- [ ] **Step 2: Write `tooling/package.json`**

```json
{
  "name": "@airavata/tooling",
  "version": "0.1.0",
  "private": true,
  "type": "module",
  "description": "Shared JS tooling configs for the Airavata Django Portal monorepo.",
  "exports": {
    "./eslint.config.js": "./eslint.config.js",
    "./prettier.config.js": "./prettier.config.js",
    "./vite.config.js": "./vite.config.js",
    "./tsconfig.base.json": "./tsconfig.base.json"
  },
  "dependencies": {
    "@eslint/js": "^9.0.0",
    "@vitejs/plugin-vue": "^5.0.0",
    "eslint": "^9.0.0",
    "eslint-config-prettier": "^9.0.0",
    "eslint-plugin-vue": "^10.0.0",
    "globals": "^15.0.0",
    "prettier": "^3.0.0",
    "typescript": "^5.0.0",
    "vite": "^6.0.0",
    "vue-eslint-parser": "^10.0.0",
    "vue-tsc": "^2.0.0"
  }
}
```

- [ ] **Step 3: Write `tooling/tsconfig.base.json`**

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "Bundler",
    "strict": true,
    "allowJs": false,
    "noEmit": true,
    "skipLibCheck": true,
    "esModuleInterop": true,
    "isolatedModules": true,
    "resolveJsonModule": true,
    "jsx": "preserve",
    "types": ["vite/client"]
  }
}
```

- [ ] **Step 4: Write `tooling/prettier.config.js`**

```js
// CommonJS because some workspaces still use CJS for prettier config.
module.exports = {
  semi: true,
  singleQuote: false,
  trailingComma: "all",
  printWidth: 100,
  tabWidth: 2,
  vueIndentScriptAndStyle: false,
};
```

- [ ] **Step 5: Write `tooling/eslint.config.js`**

```js
import js from "@eslint/js";
import vuePlugin from "eslint-plugin-vue";
import vueParser from "vue-eslint-parser";
import prettierConfig from "eslint-config-prettier";
import globals from "globals";

export default [
  js.configs.recommended,
  ...vuePlugin.configs["flat/recommended"],
  prettierConfig,
  {
    languageOptions: {
      parser: vueParser,
      ecmaVersion: 2024,
      sourceType: "module",
      globals: {
        ...globals.browser,
        ...globals.es2024,
        ...globals.node,
      },
    },
    rules: {
      "no-unused-vars": ["error", { argsIgnorePattern: "^_" }],
      "no-undef": "error",
      "no-unreachable": "error",
      "eqeqeq": ["error", "always"],
      "vue/multi-word-component-names": "off",
      "vue/no-v-html": "warn",
    },
    ignores: [
      "**/dist/**",
      "**/node_modules/**",
      "**/*.d.ts",
      "**/static/**/manifest.json",
      "**/static/common/dist/**",
    ],
  },
];
```

- [ ] **Step 6: Write `tooling/vite.config.js`**

```js
import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import { resolve } from "path";

/**
 * Shared Vite config factory for every workspace.
 *
 * @param {object} opts
 * @param {string} opts.appLabel       e.g. "django_airavata_workspace"
 * @param {string} opts.srcDir         absolute path to the workspace's JS source dir
 * @param {Record<string,string>|string} opts.entries  Rollup input(s)
 * @param {boolean} [opts.isLibrary]   true for api / plugin-api (library mode)
 * @param {object}  [opts.overrides]   shallow-merged over the generated config
 */
export function defineAppConfig({
  appLabel,
  srcDir,
  entries,
  isLibrary = false,
  overrides = {},
}) {
  const base = isLibrary ? "/" : `/static/${appLabel}/dist/`;
  return defineConfig({
    plugins: [vue()],
    base,
    build: {
      manifest: isLibrary ? false : "manifest.json",
      outDir: resolve(srcDir, `../../static/${appLabel}/dist`),
      rollupOptions: { input: entries },
    },
    css: { preprocessorOptions: { scss: { quietDeps: true } } },
    resolve: {
      extensions: [".vue", ".ts", ".js", ".json"],
      alias: { "@": srcDir },
    },
    server: { port: 9000, origin: "http://localhost:9000" },
    ...overrides,
  });
}
```

- [ ] **Step 7: Write `tooling/README.md`**

```markdown
# @airavata/tooling

Shared JavaScript tooling configs for the Airavata Django Portal monorepo.

## What it exposes

- `eslint.config.js` — ESLint 9 flat config. Strict: `@eslint/js recommended` +
  `eslint-plugin-vue/flat/recommended` + `eslint-config-prettier`.
- `prettier.config.js` — Prettier rules (printWidth 100, trailing comma, etc.).
- `vite.config.js` — exports `defineAppConfig({ appLabel, srcDir, entries, isLibrary, overrides })`
  helper. Every workspace's `vite.config.js` is a 6-10 line call to this.
- `tsconfig.base.json` — `strict: true`, `allowJs: false`. Extended by each
  Vue workspace's `jsconfig.json`.

## Consuming from a workspace

```js
// eslint.config.js
export { default } from "@airavata/tooling/eslint.config.js";
```

```js
// prettier.config.js
module.exports = require("@airavata/tooling/prettier.config.js");
```

```js
// vite.config.js
import { defineAppConfig } from "@airavata/tooling/vite.config.js";
import { resolve } from "path";

export default defineAppConfig({
  appLabel: "django_airavata_<label>",
  srcDir: resolve(import.meta.dirname, "./static/django_airavata_<label>/src"),
  entries: resolve(import.meta.dirname, "./static/django_airavata_<label>/src/main.js"),
});
```

```json
// jsconfig.json
{ "extends": "@airavata/tooling/tsconfig.base.json" }
```

## Adding a new workspace

1. Register the workspace path in the root `package.json`'s `workspaces` array.
2. Add the 4 config stanzas above.
3. Ensure the workspace's `package.json` lists `@airavata/tooling` as a
   `devDependency` (npm workspaces hoist it automatically, but the entry
   makes the dep graph explicit).
4. Run `npm install` at the repo root so the symlink is created.
```

- [ ] **Step 8: Checkpoint commit**

```bash
git add tooling/
git commit -m "wip(track-c): scaffold tooling/ workspace with shared configs"
git log --oneline -3
```

---

## Task 3: Switch Yarn 1 → npm workspaces

**Files:**
- Modify: `package.json` (root) — add tooling to workspaces, add packageManager, rewrite scripts
- Modify: `Tiltfile` — replace yarn commands with npm
- Delete: `yarn.lock`
- Create: `package-lock.json` (auto via `npm install`)

- [ ] **Step 1: Update root `package.json`**

Edit `package.json` so it reads:

```json
{
  "private": true,
  "packageManager": "npm@10.9.0",
  "workspaces": [
    "tooling",
    "django_airavata/static/common",
    "django_airavata/apps/admin",
    "django_airavata/apps/api",
    "django_airavata/apps/auth",
    "django_airavata/apps/dataparsers",
    "django_airavata/apps/workspace",
    "django_airavata/apps/workspace/django-airavata-workspace-plugin-api"
  ],
  "scripts": {
    "build": "npm run build --workspaces --if-present",
    "dev": "echo 'Use tilt up for dev servers'",
    "lint": "npm run lint --workspaces --if-present",
    "format": "prettier --write \"**/*.{js,ts,vue,json,md,scss,css}\" --ignore-path=.gitignore",
    "typecheck": "npm run typecheck --workspaces --if-present",
    "test": "npm run test --workspaces --if-present",
    "test:e2e": "echo 'test:e2e placeholder — wired up in Track Pre-A'"
  },
  "engines": {
    "node": ">=22"
  },
  "dependencies": {
    "moment": "^2.30.1"
  }
}
```

Note: the `packageManager` string uses whatever `npm --version` reports on your host. Get it with `npm --version` and substitute.

- [ ] **Step 2: Query live npm version and update the field**

```bash
NPM_V=$(npm --version)
python3 -c "
import json
d = json.load(open('package.json'))
d['packageManager'] = 'npm@$NPM_V'
open('package.json','w').write(json.dumps(d, indent=2) + '\n')
print('packageManager set to npm@$NPM_V')
"
```

- [ ] **Step 3: Delete `yarn.lock`**

```bash
rm yarn.lock
```

- [ ] **Step 4: Fresh install via npm (generates `package-lock.json`)**

```bash
rm -rf node_modules */node_modules \
       django_airavata/apps/*/node_modules \
       django_airavata/apps/workspace/django-airavata-workspace-plugin-api/node_modules \
       tooling/node_modules
npm install 2>&1 | tail -10
ls node_modules/@airavata/tooling
test -f package-lock.json && echo "OK package-lock.json created"
```
Expected: `npm install` finishes clean; `node_modules/@airavata/tooling` is a symlink to `tooling/`; `package-lock.json` exists.

- [ ] **Step 5: Update `Tiltfile`**

Find the `frontend-build` resource (around line 53) and change:

```python
    cmd='yarn install && yarn workspaces run build',
```

to:

```python
    cmd='npm install && npm run build --workspaces --if-present',
```

Then find each `frontend-<app>` resource in the `FRONTEND_APPS` loop. The current `serve_cmd='yarn run dev'` must become:

```python
        serve_cmd='npm run dev',
```

- [ ] **Step 6: Checkpoint commit**

```bash
git add package.json Tiltfile package-lock.json
git rm yarn.lock
git commit -m "wip(track-c): switch yarn 1 → npm workspaces"
```

Note: `package-lock.json` is large (~1MB). That's fine — it belongs in git per npm convention.

- [ ] **Step 7: Smoke-test that build still works via npm**

```bash
npm run build --workspaces --if-present 2>&1 | tail -15
```
Expected: all 7 workspaces build successfully.

---

## Task 4: Wire each workspace to `@airavata/tooling`

**Files:** per-workspace edits across 7 workspaces. For each workspace `W`:
- Create: `W/eslint.config.js` (re-export)
- Create: `W/prettier.config.js` (re-export)
- Create: `W/jsconfig.json` (extends)
- Replace: `W/vite.config.js` (calls `defineAppConfig`)
- Modify: `W/package.json` (add `@airavata/tooling` devDep; drop moved deps)

Workspaces and their specifics:

| Workspace | App label | srcDir suffix | Mode | Entries |
|---|---|---|---|---|
| `django_airavata/static/common` | `common` | `./js` (see notes) | library | `./js/index.js` |
| `django_airavata/apps/admin` | `django_airavata_admin` | `./static/django_airavata_admin/src` | app | `./static/django_airavata_admin/src/main.js` |
| `django_airavata/apps/api` | `django_airavata_api` | `./static/django_airavata_api/js` | library | entries object (inspect current vite.config.js) |
| `django_airavata/apps/auth` | `django_airavata_auth` | `./static/django_airavata_auth/js` | app | entries object |
| `django_airavata/apps/dataparsers` | `django_airavata_dataparsers` | `./static/django_airavata_dataparsers/js` | app | entries object |
| `django_airavata/apps/workspace` | `django_airavata_workspace` | `./static/django_airavata_workspace/js` | app | 18 entries |
| `django_airavata/apps/workspace/django-airavata-workspace-plugin-api` | `<n/a>` | `./js` | library | `./js/index.js` |

- [ ] **Step 1: Wire `django_airavata/apps/workspace` (biggest, establishes the pattern)**

Create `django_airavata/apps/workspace/eslint.config.js`:

```js
export { default } from "@airavata/tooling/eslint.config.js";
```

Create `django_airavata/apps/workspace/prettier.config.js`:

```js
module.exports = require("@airavata/tooling/prettier.config.js");
```

Create `django_airavata/apps/workspace/jsconfig.json`:

```json
{
  "extends": "@airavata/tooling/tsconfig.base.json",
  "include": ["static/django_airavata_workspace/js/**/*"]
}
```

Replace `django_airavata/apps/workspace/vite.config.js` with:

```js
import { defineAppConfig } from "@airavata/tooling/vite.config.js";
import { resolve } from "path";

const srcDir = resolve(
  import.meta.dirname,
  "./static/django_airavata_workspace/js",
);

export default defineAppConfig({
  appLabel: "django_airavata_workspace",
  srcDir,
  entries: {
    dashboard: resolve(srcDir, "entry-dashboard.js"),
    "project-list": resolve(srcDir, "entry-project-list.js"),
    applications: resolve(srcDir, "entry-applications.js"),
    "create-experiment": resolve(srcDir, "entry-create-experiment.js"),
    "view-experiment": resolve(srcDir, "entry-view-experiment.js"),
    "experiment-list": resolve(srcDir, "entry-experiment-list.js"),
    "edit-experiment": resolve(srcDir, "entry-edit-experiment.js"),
    "edit-project": resolve(srcDir, "entry-edit-project.js"),
    "user-storage": resolve(srcDir, "entry-user-storage.js"),
    compute: resolve(srcDir, "entry-compute.js"),
    datasets: resolve(srcDir, "entry-datasets.js"),
    "datasets-list": resolve(srcDir, "entry-datasets-list.js"),
    credentials: resolve(srcDir, "entry-credentials.js"),
    "gateway-settings": resolve(srcDir, "entry-gateway-settings.js"),
    "storage-detail": resolve(srcDir, "entry-storage-detail.js"),
    "compute-detail": resolve(srcDir, "entry-compute-detail.js"),
    "project-overview": resolve(srcDir, "entry-project-overview.js"),
    "application-editor": resolve(srcDir, "entry-application-editor.js"),
  },
});
```

Modify `django_airavata/apps/workspace/package.json`:
- Add `"@airavata/tooling": "*"` to `devDependencies`.
- Remove from `devDependencies`: `eslint`, `eslint-plugin-vue`, `prettier`, `vite`, `@vitejs/plugin-vue`, `vite-plugin-vue` (if present), `sass` stays (workspace-specific).

- [ ] **Step 2: Build `workspace` to verify**

```bash
cd django_airavata/apps/workspace && npm run build 2>&1 | tail -10
cd /Users/yasith/code/artisan/worktree-feat-sdk-and-devenv/airavata-portals/airavata-django-portal
python3 -c "
import json
post = set(json.load(open('django_airavata/apps/workspace/static/django_airavata_workspace/dist/manifest.json')).keys())
pre = set(open('/tmp/td-c-pre-workspace-manifest-keys.txt').read().splitlines())
assert pre == post, f'manifest drift: +{post-pre} -{pre-post}'
print('OK workspace manifest parity')
"
```
Expected: `OK workspace manifest parity`.

- [ ] **Step 3: Wire `django_airavata/apps/admin`**

Create the 4 files following the workspace pattern. The admin `vite.config.js`:

```js
import { defineAppConfig } from "@airavata/tooling/vite.config.js";
import { resolve } from "path";

export default defineAppConfig({
  appLabel: "django_airavata_admin",
  srcDir: resolve(import.meta.dirname, "./static/django_airavata_admin/src"),
  entries: resolve(
    import.meta.dirname,
    "./static/django_airavata_admin/src/main.js",
  ),
});
```

`jsconfig.json`:
```json
{
  "extends": "@airavata/tooling/tsconfig.base.json",
  "include": ["static/django_airavata_admin/src/**/*"]
}
```

`eslint.config.js` and `prettier.config.js` are identical to workspace's.

Update `package.json`: add `"@airavata/tooling": "*"`, drop the 5 moved dev deps.

Build verification:
```bash
cd django_airavata/apps/admin && npm run build && cd - > /dev/null
python3 -c "
import json
post = set(json.load(open('django_airavata/apps/admin/static/django_airavata_admin/dist/manifest.json')).keys())
pre = set(open('/tmp/td-c-pre-admin-manifest-keys.txt').read().splitlines())
assert pre == post, f'manifest drift'
print('OK admin manifest parity')
"
```

- [ ] **Step 4: Wire `django_airavata/apps/auth`**

Read the current `django_airavata/apps/auth/vite.config.js` first, mirror its entries into the `defineAppConfig` call. Create the 4 config files with the same pattern. Modify `package.json`. Build + parity-check like Step 3 (substitute `auth` for `admin`).

- [ ] **Step 5: Wire `django_airavata/apps/dataparsers`**

Same pattern as auth. Read existing vite.config.js, mirror entries, create 4 files, modify package.json, build + parity-check.

- [ ] **Step 6: Wire `django_airavata/apps/api` (library mode)**

Read the current `django_airavata/apps/api/vite.config.js`. Likely a library-mode config (produces `dist/` not in Django static). Set `isLibrary: true` in the `defineAppConfig` call. Same 4 config files, same package.json treatment.

Because api is a library, there's no `/static/<app>/dist/manifest.json` to parity-check against the Django static path; instead check `django_airavata/apps/api/dist/` (or wherever it builds to — look at the old config for the outDir). Snapshot file list before/after:

```bash
ls django_airavata/apps/api/dist 2>/dev/null | sort > /tmp/td-c-post-api-files.txt
diff /tmp/td-c-pre-api-dist /tmp/td-c-post-api-files.txt || true
```

- [ ] **Step 7: Wire `django_airavata/static/common`**

Read current vite.config.js; library-mode. Same pattern. Build + file-list parity like api.

- [ ] **Step 8: Wire `django_airavata/apps/workspace/django-airavata-workspace-plugin-api` (library mode)**

Same library-mode treatment. Build + file-list parity.

- [ ] **Step 9: Final fresh install to refresh the symlink graph**

```bash
rm -rf node_modules tooling/node_modules django_airavata/apps/*/node_modules \
       django_airavata/static/common/node_modules \
       django_airavata/apps/workspace/django-airavata-workspace-plugin-api/node_modules
npm install 2>&1 | tail -3
```
Expected: clean install.

- [ ] **Step 10: Build everything; full manifest parity gauntlet**

```bash
npm run build --workspaces --if-present 2>&1 | tail -20
for app in admin auth dataparsers workspace; do
  python3 -c "
import json
post = set(json.load(open('django_airavata/apps/$app/static/django_airavata_$app/dist/manifest.json')).keys())
pre = set(open('/tmp/td-c-pre-$app-manifest-keys.txt').read().splitlines())
assert pre == post, f'$app manifest drift: +{post-pre} -{pre-post}'
print('OK $app manifest parity')
"
done
```
Expected: 4× "OK ... manifest parity".

- [ ] **Step 11: Checkpoint commit**

```bash
git add .
git commit -m "wip(track-c): wire all 7 workspaces to @airavata/tooling"
```

---

## Task 5: Fix every ESLint 9 strict violation

**Files:** depends on what violations surface. Expected hotspots: unused imports/vars in Vue components, accidentally-global identifiers, loose equality comparisons, unreachable branches.

- [ ] **Step 1: Run the lint gauntlet to surface the full violation set**

```bash
npm run lint 2>&1 | tee /tmp/td-c-lint-raw.txt | tail -30
echo "---"
grep -E "error|warning" /tmp/td-c-lint-raw.txt | wc -l
```
Expected: possibly hundreds of errors and warnings. Record the count.

- [ ] **Step 2: Auto-fix what ESLint can**

```bash
npm run lint -- --fix 2>&1 | tail -10
# Each workspace runs `eslint <path>`, so we need the --fix per workspace.
# The root-level script above forwards it.
```

Note: because the per-workspace `lint` script is `eslint <path>`, the root's `--` forwards work. Re-run without `--fix` to confirm the remaining errors:

```bash
npm run lint 2>&1 | tee /tmp/td-c-lint-after-fix.txt | tail -30
grep -c "error" /tmp/td-c-lint-after-fix.txt
```

- [ ] **Step 3: Manually fix remaining violations**

Walk the remaining output. For each violation:

- **`no-unused-vars`** — delete the unused binding. If it's a destructured `{ a, b, c }` where only `c` is used, drop `a, b`. Prefix with `_` only for function params that must stay for signature reasons.
- **`no-undef`** — the identifier is missing from globals. Either import it, or if it's a known browser/node global that the flat config missed, add to the `globals` spread in `tooling/eslint.config.js`.
- **`no-unreachable`** — delete the dead branch.
- **`eqeqeq`** — replace `==` with `===`. If an intentional loose comparison, inline-disable with `// eslint-disable-next-line eqeqeq` + a comment explaining why.
- **`vue/no-v-html`** — warnings only, per config; only fix if a real XSS risk is plausible.
- **`vue/require-default-prop`** — add `default: null` or `default: () => ({})` to optional props.
- **`vue/no-parsing-error`** — fix the malformed template.
- **`vue/no-mutating-props`** — restructure to emit an event and let parent mutate.

After each workspace's fixes, build to confirm nothing broke:
```bash
cd django_airavata/apps/<workspace> && npm run build && cd - > /dev/null
```

If a violation is truly un-fixable in-scope (e.g., refactor required), disable it per-file with a comment explaining why:

```js
/* eslint-disable vue/no-mutating-props -- deferred to Track A rewrite */
```

- [ ] **Step 4: Confirm lint clean**

```bash
npm run lint
echo "exit=$?"
```
Expected: exit 0. If any errors remain, continue Step 3 until clean.

- [ ] **Step 5: Run Prettier check**

```bash
npx prettier --check . 2>&1 | tail -10
```
Expected: all files listed as "matches". If any "code style issues" appear:

```bash
npm run format   # writes fixes
npx prettier --check .
```
Expected: exit 0.

- [ ] **Step 6: Re-build everything; re-verify manifest parity**

```bash
npm run build --workspaces --if-present 2>&1 | tail -15
for app in admin auth dataparsers workspace; do
  python3 -c "
import json
post = set(json.load(open('django_airavata/apps/$app/static/django_airavata_$app/dist/manifest.json')).keys())
pre = set(open('/tmp/td-c-pre-$app-manifest-keys.txt').read().splitlines())
assert pre == post
print('OK $app manifest parity')
"
done
```
Expected: 4× OK.

- [ ] **Step 7: Checkpoint commit**

```bash
git add .
git commit -m "wip(track-c): fix every ESLint 9 strict violation across 7 workspaces"
```

---

## Task 6: Run `typecheck` and `test`

**Files:** none (verification only).

- [ ] **Step 1: Run vue-tsc across all workspaces**

```bash
npm run typecheck 2>&1 | tail -10
```
Expected: each workspace reports either "0 files" (no `.ts` yet) or passes. Exit 0 overall.

- [ ] **Step 2: Run vitest suites**

```bash
npm run test 2>&1 | tail -20
```
Expected: the workspaces that define `test:unit` (api, workspace per the survey) run vitest and pass. Exit 0 overall.

- [ ] **Step 3: Run `test:e2e` placeholder**

```bash
npm run test:e2e
```
Expected: prints `test:e2e placeholder — wired up in Track Pre-A`; exit 0.

- [ ] **Step 4: Checkpoint commit (only if verification required any tweaks — else skip)**

If any vitest adjustment was needed (e.g., a test imported a removed devDep):

```bash
git add .
git commit -m "wip(track-c): fix vitest suites after devDep hoisting"
```

---

## Task 7: Run every gate check

**Files:** none (verification only; produces pass/fail for each of 15 checks).

Execute the 15 gate checks from the spec's "Done criteria" section. Record each exit status.

- [ ] **Step 1: Gates 1-3 — `tooling/` structure and workspace wiring**

```bash
echo "=== Gate 1: tooling/ files ===" && \
test -d tooling \
  && test -f tooling/package.json \
  && test -f tooling/eslint.config.js \
  && test -f tooling/prettier.config.js \
  && test -f tooling/vite.config.js \
  && test -f tooling/tsconfig.base.json \
  && test -f tooling/README.md \
  && echo OK-gate-1

echo "=== Gate 2: tooling in workspaces ===" && \
python3 -c "
import json
ws = json.load(open('package.json')).get('workspaces', [])
assert 'tooling' in ws, f'not in: {ws}'
print('OK-gate-2')
"

echo "=== Gate 3: all 7 workspaces wired ===" && \
for ws in django_airavata/static/common \
          django_airavata/apps/admin \
          django_airavata/apps/api \
          django_airavata/apps/auth \
          django_airavata/apps/dataparsers \
          django_airavata/apps/workspace \
          django_airavata/apps/workspace/django-airavata-workspace-plugin-api; do
  grep -q "@airavata/tooling" "$ws/eslint.config.js" \
    && grep -q "@airavata/tooling" "$ws/prettier.config.js" \
    && grep -q "@airavata/tooling" "$ws/vite.config.js" \
    || { echo "FAIL $ws"; exit 1; }
done
echo OK-gate-3
```

- [ ] **Step 2: Gates 4-7 — package manager switch artifacts**

```bash
echo "=== Gate 4: packageManager=npm ===" && \
python3 -c "
import json
pm = json.load(open('package.json')).get('packageManager', '')
assert pm.startswith('npm@'), f'got: {pm!r}'
print('OK-gate-4', pm)
"

echo "=== Gate 5: yarn.lock gone; package-lock.json present ===" && \
test ! -f yarn.lock && test -f package-lock.json && echo OK-gate-5

echo "=== Gate 6: root scripts exist ===" && \
python3 -c "
import json
s = json.load(open('package.json'))['scripts']
missing = [n for n in ('lint','format','typecheck','test','test:e2e') if n not in s]
assert not missing, f'missing: {missing}'
print('OK-gate-6')
"

echo "=== Gate 7: Tiltfile yarn-free ===" && \
c=$(grep -c '\byarn\b' Tiltfile); \
test "$c" = "0" && echo OK-gate-7 || echo "FAIL: $c yarn mentions in Tiltfile"
```

- [ ] **Step 3: Gates 8-12 — install / lint / format / typecheck / build**

```bash
echo "=== Gate 8: fresh npm install ===" && \
rm -rf node_modules tooling/node_modules \
       django_airavata/apps/*/node_modules \
       django_airavata/static/common/node_modules \
       django_airavata/apps/workspace/django-airavata-workspace-plugin-api/node_modules && \
npm install 2>&1 | tail -3 && \
echo OK-gate-8

echo "=== Gate 9: lint ===" && \
npm run lint 2>&1 | tail -5 && echo OK-gate-9

echo "=== Gate 10: prettier ===" && \
npx prettier --check . 2>&1 | tail -5 && echo OK-gate-10

echo "=== Gate 11: typecheck ===" && \
npm run typecheck 2>&1 | tail -5 && echo OK-gate-11

echo "=== Gate 12: build ===" && \
npm run build --workspaces --if-present 2>&1 | tail -10 && echo OK-gate-12
```

- [ ] **Step 4: Gates 13-15 — manifest parity, tests, stray configs**

```bash
echo "=== Gate 13: manifest parity ===" && \
for app in admin auth dataparsers workspace; do
  python3 -c "
import json
post = set(json.load(open('django_airavata/apps/$app/static/django_airavata_$app/dist/manifest.json')).keys())
pre = set(open('/tmp/td-c-pre-$app-manifest-keys.txt').read().splitlines())
assert pre == post, f'$app manifest drift'
"
done
echo OK-gate-13

echo "=== Gate 14: tests ===" && \
npm run test 2>&1 | tail -10 && echo OK-gate-14

echo "=== Gate 15: no stray legacy config files ===" && \
found=$(find . -maxdepth 4 \( -name '.eslintrc*' -o -name '.prettierrc*' \) \
  -not -path '*/node_modules/*')
test -z "$found" && echo OK-gate-15 || { echo "FAIL stray: $found"; exit 1; }
```

If any gate fails, investigate and fix. Do not move to Task 8 until all 15 are OK.

---

## Task 8: Squash and merge

**Files:** none (git history rewrite + merge).

- [ ] **Step 1: Verify the checkpoint commits**

```bash
git log --oneline -8
```
Expected sequence (bottom to top):
- `f5d19f7942 docs(track-c): monorepo tooling design spec`
- one Task-2 commit: `wip(track-c): scaffold tooling/ workspace with shared configs`
- one Task-3 commit: `wip(track-c): switch yarn 1 → npm workspaces`
- one Task-4 commit: `wip(track-c): wire all 7 workspaces to @airavata/tooling`
- one Task-5 commit: `wip(track-c): fix every ESLint 9 strict violation across 7 workspaces`
- optionally one Task-6 commit

- [ ] **Step 2: Count the wip commits (for the soft-reset depth)**

```bash
COUNT=$(git log --oneline "$(git merge-base HEAD modernization)..HEAD" | \
  grep -c "^[a-f0-9]* wip(track-c):")
echo "wip commits: $COUNT"
```

- [ ] **Step 3: Soft-reset to the spec commit**

```bash
git reset --soft "$(git log --format=%H --grep='docs(track-c): monorepo tooling design spec' -n 1)"
git status --short | head
```
Expected: HEAD is the spec commit; all Track C tooling changes remain staged.

- [ ] **Step 4: Count the staged footprint (sanity check)**

```bash
git diff --cached --stat | tail -3
```
Expected: many files (tooling/ + 7 workspaces + root package.json + Tiltfile + package-lock.json + yarn.lock deletion).

- [ ] **Step 5: Create the single Track C commit**

```bash
git commit -m "$(cat <<'EOF'
refactor(portal): monorepo tooling

- Introduce tooling/ workspace (@airavata/tooling) hosting shared configs:
  eslint.config.js (flat, strict, ESLint 9); prettier.config.js (shared
  rules); vite.config.js (exports defineAppConfig({appLabel, srcDir,
  entries, isLibrary, overrides})); tsconfig.base.json (strict:true,
  allowJs:false).
- Switch monorepo from Yarn 1 classic to npm workspaces. Delete yarn.lock;
  introduce package-lock.json. Pin packageManager=npm@<host>. Update root
  scripts (lint/format/typecheck/test/test:e2e/build) to use
  `npm run X --workspaces --if-present`. Update Tiltfile to run npm instead
  of yarn. DEVIATION from umbrella guardrail "Yarn 1 classic" —
  justification in spec.
- Wire all 7 existing workspaces to @airavata/tooling: per-workspace
  eslint.config.js / prettier.config.js / jsconfig.json now re-export or
  extend from the shared package; vite.config.js replaced with a 6-10 line
  defineAppConfig() call.
- Drop moved devDeps (eslint, eslint-plugin-vue, prettier, vite,
  @vitejs/plugin-vue) from each workspace's package.json — they now live
  only in tooling/ and hoist via npm workspaces.
- Fix every ESLint 9 strict violation surfaced by the new baseline (the
  previous yarn-era lint scripts were broken because no config files
  existed).

Functional parity: manifest keys byte-identical for all Django apps; all
workspaces build via `npm run build --workspaces`; typecheck passes (0
files until Track A). Track A will extend tsconfig.base.json and flip .js
→ .ts across ~178 Vue files.

Spec: docs/superpowers/specs/2026-04-21-track-c-monorepo-tooling-design.md
EOF
)"
```

- [ ] **Step 6: Push + merge to modernization**

```bash
git push -u origin track-c/monorepo-tooling
git checkout modernization
git pull origin modernization
git merge --no-ff track-c/monorepo-tooling -m "merge: Track C (monorepo tooling)"
git push origin modernization
```

- [ ] **Step 7: Amend umbrella spec to reflect the Yarn→npm deviation**

Edit `docs/superpowers/specs/2026-04-21-portal-modernization-design.md`:
- Update the Track C section to say "npm workspaces" instead of "Yarn 1 classic".
- Update the Guardrails section: strike "Yarn 1 classic", add a note that Track C switched to npm workspaces with rationale in its own spec.

Commit on modernization:
```bash
git add docs/superpowers/specs/2026-04-21-portal-modernization-design.md
git commit -m "docs(umbrella): Track C switched to npm workspaces (deviates from Yarn 1 guardrail)"
git push origin modernization
```

- [ ] **Step 8: Final verification**

```bash
git log --oneline --merges -3
```
Expected: top merge commit is `merge: Track C (monorepo tooling)`; previous is `merge: Track D (Python hygiene)`.

---

## Plan Self-Review

**Spec coverage:**

| Spec section | Plan task |
|---|---|
| Scope 1: Create tooling/ workspace | Task 2 |
| Scope 2: Yarn → npm switch | Task 3 |
| Scope 3: Wire all 7 workspaces | Task 4 |
| Scope 4: Fix ESLint strict violations | Task 5 |
| Scope 5: Root scripts | Task 3 Step 1 (scripts block) + Task 6 verifications |
| Scope 6: tooling/README.md | Task 2 Step 7 |
| Testing Layer 1 (fresh install) | Task 3 Step 4 + Task 7 Step 3 (Gate 8) |
| Testing Layer 2 (build parity) | Task 1 (baseline) + Task 4 (per-workspace) + Task 7 Step 4 (Gate 13) |
| Testing Layer 3 (lint/typecheck/tests green) | Task 5 + Task 6 + Task 7 Steps 3-4 |
| Testing Layer 4 (Tilt boots) | Task 3 Step 5 + ad-hoc `tilt up` after merge |
| Done criteria (15 gate checks) | Task 7 |
| Amend umbrella guardrail "Yarn 1 classic" | Task 8 Step 7 |

Every spec requirement maps to at least one task.

**Placeholder scan:** grep for `TBD`, `TODO`, `FIXME`, `fill in`, `similar to` — none remain. Each step contains either concrete code or a concrete shell command with expected output. The only phrase approaching a placeholder is Task 4 Step 6's "look at the old config for the outDir" — retained intentionally because the library-mode outDir varies by workspace and the implementer should inspect the existing vite.config.js which remains unmodified at that point.

**Type consistency:** branch name `track-c/monorepo-tooling`, shared package name `@airavata/tooling`, and all 7 workspace paths are stable across tasks. `defineAppConfig()` signature matches between spec Section 2.4 and plan Task 2 Step 6 and plan Task 4 Step 1. Gate check numbering 1-15 matches between spec "Done criteria" and Task 7.

---

## Execution handoff

Plan complete and saved to `airavata-django-portal/docs/superpowers/plans/2026-04-21-track-c-monorepo-tooling-plan.md`. Recommended execution: `superpowers:subagent-driven-development` with a fresh subagent per task.
