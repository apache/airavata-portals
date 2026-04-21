# Track C — Monorepo Tooling Design

> Track C of the portal modernization umbrella. Umbrella spec:
> `docs/superpowers/specs/2026-04-21-portal-modernization-design.md`.

## Goal

Stand up a shared `tooling/` workspace hosting all cross-workspace JS-side
configuration, fix the currently-broken `yarn lint` surface, switch the
monorepo from Yarn 1 to npm workspaces, and introduce the TypeScript +
vue-tsc pipeline Track A will build on. Functional-parity guardrail: built
artefacts and manifests stay logically identical.

## Scope

One squashed commit on `track-c/monorepo-tooling`.

### 1. Create the `tooling/` workspace

Single package `@airavata/tooling`, private, at `tooling/`:

```
tooling/
├── package.json
├── eslint.config.js
├── prettier.config.js
├── vite.config.js
├── tsconfig.base.json
└── README.md
```

`tooling/package.json`:

```json
{
    "name": "@airavata/tooling",
    "version": "0.1.0",
    "private": true,
    "type": "module",
    "exports": {
        "./eslint.config.js": "./eslint.config.js",
        "./prettier.config.js": "./prettier.config.js",
        "./vite.config.js": "./vite.config.js",
        "./tsconfig.base.json": "./tsconfig.base.json"
    },
    "dependencies": {
        "@eslint/js": "^9",
        "@vitejs/plugin-vue": "^5",
        "eslint": "^9",
        "eslint-config-prettier": "^9",
        "eslint-plugin-vue": "^10",
        "globals": "^15",
        "prettier": "^3",
        "typescript": "^5",
        "vite": "^6",
        "vue-eslint-parser": "^10",
        "vue-tsc": "^2"
    }
}
```

Dev dependencies are pinned at the `tooling/` workspace so every downstream
workspace inherits them via npm's workspace hoisting.

### 2. Switch Yarn 1 → npm workspaces

This is a **deliberate deviation from the umbrella guardrail "Yarn 1 classic"**.
Rationale: simpler onboarding (npm ships with Node — no corepack needed),
aligns with Node-ecosystem defaults, drops a maintenance tool. The umbrella
spec will be amended at Track C merge time.

Changes:

- Delete `yarn.lock`; `npm install` produces `package-lock.json`.
- Replace root `package.json` scripts that use `yarn workspaces run X` with
  `npm run X --workspaces --if-present`.
- Update `Tiltfile`: `frontend-build` resource's `yarn install && yarn workspaces run build`
  → `npm install && npm run build --workspaces --if-present`.
- Update per-workspace serve commands in Tiltfile that hardcode `yarn run dev`
  → `npm run dev`.
- Add `"packageManager": "npm@<host-version>"` to root `package.json`.
- Update any README/CONTRIBUTING that mentions `yarn`.

### 3. Shared ESLint 9 flat config

**Posture:** strict from day one (Q3-a). Single flat-config array with
`.vue` rules scoped via `files:` globs.

`tooling/eslint.config.js`:

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
            globals: { ...globals.browser, ...globals.es2024, ...globals.node },
        },
        rules: {
            "no-unused-vars": ["error", { argsIgnorePattern: "^_" }],
            "no-undef": "error",
            "no-unreachable": "error",
            eqeqeq: ["error", "always"],
            "vue/multi-word-component-names": "off",
            "vue/no-v-html": "warn",
        },
        ignores: [
            "**/dist/**",
            "**/node_modules/**",
            "**/*.d.ts",
            "**/static/**/manifest.json",
        ],
    },
];
```

Each consuming workspace has a minimal `eslint.config.js`:

```js
export { default } from "@airavata/tooling/eslint.config.js";
```

All ESLint violations surfaced by the first strict run are fixed in this
same commit.

### 4. Shared Prettier config

`tooling/prettier.config.js`:

```js
module.exports = {
    semi: true,
    singleQuote: false,
    trailingComma: "all",
    printWidth: 100,
    tabWidth: 2,
    vueIndentScriptAndStyle: false,
};
```

Each workspace: `module.exports = require("@airavata/tooling/prettier.config.js");`.

### 5. Shared Vite config helper

`tooling/vite.config.js` exports a factory `defineAppConfig(opts)`:

```js
import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import { resolve } from "path";

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

Each workspace's `vite.config.js` becomes a 3-10 line call. Example for `admin`:

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

Library-mode example for `django-airavata-api` (no manifest, no base prefix):

```js
export default defineAppConfig({
    appLabel: "django_airavata_api",
    srcDir: resolve(import.meta.dirname, "./static/django_airavata_api/js"),
    entries: resolve(
        import.meta.dirname,
        "./static/django_airavata_api/js/index.js",
    ),
    isLibrary: true,
});
```

### 6. TypeScript foundation

`tooling/tsconfig.base.json`:

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

**Posture:** `strict: true`, `allowJs: false` (Q6-b). This means Track A
must convert files in dependency order — a `.ts` file cannot import from
an unconverted `.js` file once vue-tsc is enforcing.

Until Track A lands, no `.ts` files exist, so `vue-tsc --noEmit` exits 0
("0 files checked") per workspace.

Each Vue workspace adds a `jsconfig.json` that extends the base (IDE-only
during Track C — no `.ts` files exist yet):

```json
{ "extends": "@airavata/tooling/tsconfig.base.json" }
```

This gives IDEs path-alias resolution (`@/...`) and surfaces the strict
rules in the editor before Track A even starts.

### 7. Root scripts

Root `package.json` gets all five scripts wired (Q7-a):

```json
{
    "scripts": {
        "lint": "npm run lint --workspaces --if-present",
        "format": "prettier --write \"**/*.{js,ts,vue,json,md,scss,css}\" --ignore-path=.gitignore",
        "typecheck": "npm run typecheck --workspaces --if-present",
        "test": "npm run test --workspaces --if-present",
        "test:e2e": "echo 'test:e2e placeholder — wired up in Track Pre-A'",
        "build": "npm run build --workspaces --if-present"
    }
}
```

Per-workspace `lint`/`typecheck`/`test`/`build` scripts stay intact so devs
can run in a single workspace.

### 8. Documentation

New `tooling/README.md` (~30 lines) covering:

- What `@airavata/tooling` exposes
- How to add a new workspace (`eslint.config.js`, `prettier.config.js`,
  `vite.config.js`, `jsconfig.json` stanzas)
- The npm workspace switchover (commands a dev needs to know)

## Out of scope

- Vue Composition API / TypeScript conversion (Track A).
- Library swaps (moment → date-fns, etc. — Track B).
- Playwright setup (Track Pre-A).
- Any behavioural change (route, build output, CSS output, rendered HTML).

## Design decisions

| #   | Decision                                              | Alternatives                                           |
| --- | ----------------------------------------------------- | ------------------------------------------------------ |
| Q1  | Single `tooling/` workspace with all 4 shared configs | 4 sub-workspaces; flat files at repo root              |
| Q2  | Single flat `eslint.config.js` export                 | Layered base/vue/ts exports; plugin-preset passthrough |
| Q3  | Strict from day one; fix every violation in Track C   | Minimal-safe baseline; Prettier-compatible recommended |
| Q4  | Shared `defineAppConfig()` Vite helper                | Vite `mergeConfig()` pattern; leave vite alone         |
| Q5  | Switch Yarn 1 → npm workspaces                        | Stay on Yarn 1 + corepack; switch to pnpm              |
| Q6  | `strict: true, allowJs: false`                        | `allowJs: true` for gradual migration; two tsconfigs   |
| Q7  | All 5 root scripts now; `test:e2e` is a placeholder   | Defer `test:e2e` to Track Pre-A; no-op stubs           |
| Q8  | One squashed commit for Track C                       | Three logical commits; per-change commits              |

## Testing protocol

### Layer 1 — Fresh npm install

```bash
rm -rf node_modules */node_modules django_airavata/apps/*/node_modules \
       django_airavata/apps/workspace/django-airavata-workspace-plugin-api/node_modules \
       tooling/node_modules
npm install
ls node_modules/@airavata/tooling   # workspace is symlinked in
```

### Layer 2 — Build parity

Per-workspace `dist/` logical-entry set must stay identical.

```bash
# Pre-Track-C baseline on modernization (before any Track C work).
git checkout modernization
yarn install && yarn workspaces run build
for app in admin api auth dataparsers workspace; do
  cp -r "django_airavata/apps/$app/static/django_airavata_$app/dist" \
     "/tmp/td-c-pre-$app-dist"
done
cp -r django_airavata/static/common/dist /tmp/td-c-pre-common-dist

# Post-Track-C on track-c/monorepo-tooling.
git checkout track-c/monorepo-tooling
npm install
npm run build --workspaces --if-present

# Manifest key parity (ignore minified-filename hashes).
for app in admin auth dataparsers workspace; do
  python3 -c "
import json
pre = json.load(open('/tmp/td-c-pre-$app-dist/manifest.json'))
post = json.load(open('django_airavata/apps/$app/static/django_airavata_$app/dist/manifest.json'))
assert set(pre.keys()) == set(post.keys()), \
  f'$app manifest drift: +{set(post.keys())-set(pre.keys())} -{set(pre.keys())-set(post.keys())}'
print('OK $app manifest parity')
"
done
```

### Layer 3 — Lint / typecheck / tests green

```bash
npm run lint       # all clean (strict + Vue recommended)
npm run format -- --check .
npm run typecheck  # 0 files each — passes trivially
npm run test       # vitest suites where defined
```

### Layer 4 — Tilt still boots

Spot-check `tilt up`:

- `frontend-build` resource runs npm commands, not yarn.
- `frontend-<app>` resources still start Vite dev server on port 9000.
- Portal at `localhost:8000` serves built bundles identically.

No curl smoke suite — build-output/manifest parity is stronger evidence for
a tooling-only change.

### Rollback

- Any Layer 2 manifest drift → revert the Track C merge.
- Layer 3 lint errors that slipped through → fix in a follow-up commit on
  `track-c/monorepo-tooling` before merging.

## Done criteria (gate checks)

These are the exact checks the umbrella plan's Task 2 Step 5 runs:

```bash
# 1. tooling/ workspace exists with all 4 configs + README.
test -d tooling \
  && test -f tooling/package.json \
  && test -f tooling/eslint.config.js \
  && test -f tooling/prettier.config.js \
  && test -f tooling/vite.config.js \
  && test -f tooling/tsconfig.base.json \
  && test -f tooling/README.md

# 2. tooling/ registered as a workspace.
python3 -c "
import json
ws = json.load(open('package.json')).get('workspaces', [])
assert 'tooling' in ws, f'tooling/ not in workspaces: {ws}'
print('OK')
"

# 3. Every existing workspace consumes @airavata/tooling in all 3 configs.
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
    || { echo "FAIL: $ws not wired"; exit 1; }
done
echo "OK 7 workspaces wired"

# 4. packageManager pinned to npm.
python3 -c "
import json
pm = json.load(open('package.json')).get('packageManager', '')
assert pm.startswith('npm@'), f'expected npm@..., got {pm!r}'
print('OK', pm)
"

# 5. No yarn.lock; package-lock.json present.
test ! -f yarn.lock && test -f package-lock.json

# 6. Root-level scripts exist.
python3 -c "
import json
d = json.load(open('package.json'))['scripts']
missing = [s for s in ('lint','format','typecheck','test','test:e2e') if s not in d]
assert not missing, f'missing: {missing}'
print('OK')
"

# 7. Tiltfile no longer invokes yarn.
test $(grep -c '\byarn\b' Tiltfile) -eq 0

# 8. Fresh npm install succeeds.
rm -rf node_modules django_airavata/**/node_modules tooling/node_modules
npm install
# Expected: exit 0.

# 9. ESLint 9 flat config — strict, clean across all 7 workspaces.
npm run lint
# Expected: exit 0, no errors.

# 10. Prettier check clean.
npx prettier --check .
# Expected: exit 0.

# 11. vue-tsc strict passes (0 files each).
npm run typecheck
# Expected: exit 0.

# 12. Every workspace builds.
npm run build --workspaces --if-present

# 13. Manifest key parity vs pre-Track-C baseline.
#     (Checked in Testing Layer 2 above; re-run here.)
for app in admin auth dataparsers workspace; do
  python3 -c "
import json
pre = json.load(open('/tmp/td-c-pre-$app-dist/manifest.json'))
post = json.load(open('django_airavata/apps/$app/static/django_airavata_$app/dist/manifest.json'))
assert set(pre.keys()) == set(post.keys()), f'$app manifest drift'
"
done

# 14. vitest suites (where defined) pass.
npm run test
# Expected: exit 0.

# 15. No stray legacy config files duplicating tooling/.
find . -maxdepth 4 \( -name '.eslintrc*' -o -name '.prettierrc*' \) \
  -not -path '*/node_modules/*' | head
# Expected: empty.
```

## Risks and mitigations

| Risk                                                                                      | Mitigation                                                                                                                 |
| ----------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| ESLint 9 strict surfaces so many violations we can't land the track in one commit         | Layer 3 testing exposes the blast radius early; if >200 violations need manual fixes, pause and re-brainstorm cadence (Q8) |
| npm workspaces behave differently from Yarn workspaces on Tilt's hot-reload path          | Layer 4 spot-check; falls back to rerunning `npm install` if hoisting issues appear                                        |
| Manifest drift after build (a build-time plugin behaves differently under npm workspaces) | Layer 2 parity check catches byte-identical key drift                                                                      |
| `"packageManager": "npm@..."` field not honoured because corepack isn't installed         | Harmless — the field becomes documentation-only when corepack is absent                                                    |
| Umbrella "Yarn 1 classic" guardrail deviation                                             | Explicit: amend umbrella spec at Track C merge time (not here) to reflect npm switch                                       |
| vue-tsc `strict:true,allowJs:false` makes Track A's dependency-order migration harder     | Track A's own spec will plan conversion order leaves-first; this spec simply documents the constraint                      |
