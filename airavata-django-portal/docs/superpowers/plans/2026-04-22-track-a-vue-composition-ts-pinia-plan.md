# Track A — Vue Composition + TypeScript + Pinia Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Land the Vue 2-era → Vue 3 Composition + TypeScript + Pinia rewrite on `track-a/vue-composition-ts-pinia` as one squashed commit on `modernization`. Scale: 179 `.vue`, 76+86 `.js`, 8 Vuex stores → ~3 Pinia stores.

**Architecture:** 7 internal milestones, each a `wip(track-a):` checkpoint commit. Strict leaves-first order enforced by per-milestone `npm run typecheck` under `allowJs:false`. Final step squashes to one commit. Zero tolerance `@ts-expect-error` at end.

**Tech Stack:** Vue 3 Composition API (`<script setup lang="ts">`) / Pinia / TypeScript strict / Vite 6 / vue-tsc 2 / Track Pre-A's Vitest + Playwright harness as safety net.

**Spec:** `docs/superpowers/specs/2026-04-22-track-a-vue-composition-ts-pinia-design.md`

**Working directory for every command:** `airavata-portals/airavata-django-portal`.

**Starting branch:** `track-a/vue-composition-ts-pinia`, HEAD at `c17520fb0e docs(track-a): Vue Composition + TS + Pinia design spec`.

---

## File Structure

### New files

- `django_airavata/static/common/js/stores/user.ts` — consolidated user + extendedUserProfile Pinia store.
- `django_airavata/static/common/js/stores/experiment.ts` — consolidated viewExperiment Pinia store.
- `django_airavata/static/common/js/stores/webComponents.ts` — standalone workspace web-components Pinia store.
- `django_airavata/static/common/js/types/*.ts` — type definition files for User, Project, Experiment, etc., as milestone 1 surfaces the need.
- Archive of the wip commit sequence: `docs/superpowers/track-a-wip-commits.patch` (created at squash time for bisect reference).

### Modified files (counts)

- 179 `.vue` files → `<script setup lang="ts">`.
- ~76 utility `.js` files → `.ts` (leaves-first subset).
- 86 API model `.js` files → `.ts`.
- 8 Vuex store `.js` files deleted (store/index.js + modules in auth/workspace/admin).
- Consumer files (~20) migrated from `mapGetters`/`mapActions` → `useStore()`.
- `package.json` in each workspace: `vuex` removed; `pinia` added where consumed.
- `tooling/eslint.config.js` (milestone 7): demoted rules re-elevated to error.

### Deleted

- `django_airavata/apps/auth/static/django_airavata_auth/js/store/` (entire directory).
- `django_airavata/apps/workspace/static/django_airavata_workspace/js/store/` (entire directory).
- `django_airavata/apps/workspace/static/django_airavata_workspace/js/web-components/store.js`.
- `django_airavata/apps/admin/static/django_airavata_admin/src/store/` (entire directory).

---

## Task 0: Capture pre-Track-A baseline

**Files:** none (produces `/tmp/td-a-pre-*-manifest-keys.txt`, `/tmp/td-a-pre-*-size.txt`, `/tmp/td-a-pre-test-summary.txt`).

- [ ] **Step 1: Verify clean state**

```bash
cd /Users/yasith/code/artisan/worktree-feat-sdk-and-devenv/airavata-portals/airavata-django-portal
git status --porcelain
git branch --show-current
```
Expected: empty status; branch `track-a/vue-composition-ts-pinia`.

- [ ] **Step 2: Build + snapshot manifests + bundle sizes**

```bash
npm install 2>&1 | tail -3
npm run build --workspaces --if-present 2>&1 | tail -10
rm -f /tmp/td-a-pre-*
for app in admin auth dataparsers workspace; do
  python3 -c "
import json
keys = sorted(k for k in json.load(open('django_airavata/apps/$app/static/django_airavata_$app/dist/manifest.json')) if not k.startswith('_'))
open('/tmp/td-a-pre-$app-manifest-keys.txt', 'w').write('\n'.join(keys) + '\n')
print('$app:', len(keys))
"
  du -s django_airavata/apps/$app/static/django_airavata_$app/dist/assets \
    > /tmp/td-a-pre-$app-size.txt
done
```

- [ ] **Step 3: Snapshot test suite counts**

```bash
npm run test 2>&1 | tee /tmp/td-a-pre-test-summary.txt | tail -5
```
Expected: current baseline — at least the 2 api + 2 ProjectListItem tests from Track Pre-A.

- [ ] **Step 4: Record .vue / .js file counts (for reconciliation at end)**

```bash
find django_airavata -name '*.vue' -not -path '*/node_modules/*' -not -path '*/dist/*' | wc -l | tee /tmp/td-a-pre-vue-count.txt
find django_airavata/apps/api/static/django_airavata_api/js/models -name '*.js' -not -path '*/dist/*' | wc -l | tee /tmp/td-a-pre-models-count.txt
```
Expected: 179 .vue; 86 models.

---

## Task 1 — Milestone 1: Utility leaves `.js` → `.ts`

**Goal:** Convert every `.js` file that has no internal imports, or only imports already-`.ts` files. This is the prerequisite for every other file to become `.ts`.

### Exact pattern per file

For each leaf `.js` file:

1. Read the file.
2. Rename to `.ts`.
3. Add explicit type annotations on function parameters, return types, and exported constants.
4. If the file used CJS (`module.exports`), convert to ESM (`export default ...` / `export const ...`).
5. Update every import of this file to drop the `.js` extension (TS handles resolution).
6. Run `npm run typecheck` locally in the workspace.

### Order of conversion

Leaves first. Recommended sequence per workspace:

**common workspace** (18 files):
- `static/common/js/utils/urls.js` → `urls.ts`
- `static/common/js/utils/dates.js` → `dates.ts`
- `static/common/js/utils/debounce.js` → `debounce.ts` (if exists — else skip)
- ... continue per a `node -e "console.log(require('madge')(...))"` dependency ordering (use `npx madge --image /tmp/common-deps.svg <dir>` or manual inspection).

**Each of admin/auth/dataparsers/workspace:**
- Workspace-local utilities with no cross-workspace imports.

- [ ] **Step 1: Enumerate util `.js` files by workspace**

```bash
for ws in django_airavata/static/common django_airavata/apps/admin/static/django_airavata_admin/src django_airavata/apps/auth/static/django_airavata_auth/js django_airavata/apps/dataparsers/static/django_airavata_dataparsers/js django_airavata/apps/workspace/static/django_airavata_workspace/js; do
  echo "--- $ws ---"
  find $ws -name '*.js' -not -path '*/node_modules/*' -not -path '*/dist/*' -not -path '*/tests/*' -not -path '*/entry-*' | head -30
done
```
Expected: printed list of leaf candidates.

- [ ] **Step 2: Convert each file (example: `dates.js` → `dates.ts`)**

For `django_airavata/static/common/js/utils/dates.js`:

```bash
git mv django_airavata/static/common/js/utils/dates.js django_airavata/static/common/js/utils/dates.ts
```

Edit the new `.ts` file. Update function signatures with types:

```ts
const EN = "en-US";
const UNITS: ReadonlyArray<{ limit: number; unit: Intl.RelativeTimeFormatUnit; div: number }> = [
  { limit: 60, unit: "second", div: 1 },
  { limit: 3600, unit: "minute", div: 60 },
  { limit: 86400, unit: "hour", div: 3600 },
  { limit: 2592000, unit: "day", div: 86400 },
  { limit: 31536000, unit: "month", div: 2592000 },
  { limit: Infinity, unit: "year", div: 31536000 },
];

export function relativeTime(date: string | number | Date, now: Date = new Date()): string {
  const deltaSec = (new Date(date).getTime() - now.getTime()) / 1000;
  const abs = Math.abs(deltaSec);
  const u = UNITS.find((u) => abs < u.limit) ?? UNITS[UNITS.length - 1];
  const value = Math.round(deltaSec / u.div);
  return new Intl.RelativeTimeFormat(EN, { numeric: "auto" }).format(value, u.unit);
}

export function formatShort(date: string | number | Date): string {
  return new Intl.DateTimeFormat(EN, { dateStyle: "medium", timeStyle: "short" }).format(new Date(date));
}

export function formatDate(date: string | number | Date): string {
  return new Intl.DateTimeFormat(EN, { month: "short", day: "numeric", year: "numeric" }).format(new Date(date));
}

export function formatIsoDate(date: string | number | Date): string {
  return new Date(date).toISOString().slice(0, 10);
}

export function formatUtc(date: string | number | Date): string {
  return new Date(date).toISOString().replace(/\.\d{3}Z$/, "Z");
}
```

Update every importer to remove `.js` extension. Find them:

```bash
grep -rln "utils/dates\.js" django_airavata --include='*.vue' --include='*.js' --include='*.ts' \
  | grep -v node_modules | grep -v dist
```

Replace `"..../utils/dates.js"` → `"..../utils/dates"` (or keep `.js` but add `.ts` extension support — confirm the existing vite config supports extensionless imports; `tsconfig.base.json` already lists `".ts"` first in `extensions`).

- [ ] **Step 3: Repeat for remaining utility leaves**

Work through the enumeration from Step 1. Skip files that import other non-converted `.js` files — those get converted later in this milestone once their imports are `.ts`.

- [ ] **Step 4: Run typecheck**

```bash
npm run typecheck 2>&1 | tail -20
```
Expected: exit 0 (vue-tsc in strict mode passes).

If it fails because a `.ts` file imports from a `.js` file that hasn't been converted yet, identify that `.js` file and convert it first, then re-run.

- [ ] **Step 5: Run lint + build + tests**

```bash
npm run lint 2>&1 | tail -3
npm run build --workspaces --if-present 2>&1 | tail -5
npm run test 2>&1 | tail -5
```
Expected: all exit 0.

- [ ] **Step 6: Manifest parity check**

```bash
for app in admin auth dataparsers workspace; do
  python3 -c "
import json
pre = {k for k in open('/tmp/td-a-pre-$app-manifest-keys.txt').read().splitlines() if k and not k.startswith('_')}
post = {k for k in json.load(open('django_airavata/apps/$app/static/django_airavata_$app/dist/manifest.json')) if not k.startswith('_')}
assert pre == post, f'$app manifest drift'
print('OK $app')
"
done
```
Expected: 4× OK.

- [ ] **Step 7: Checkpoint commit**

```bash
git add -A
git commit -m "wip(track-a): utility leaves .js → .ts"
git log --oneline -3
```

---

## Task 2 — Milestone 2: API models `.js` → `.ts`

**Goal:** Convert the 86 model files in `django_airavata/apps/api/static/django_airavata_api/js/models/` to `.ts`. These are the biggest `.js` batch; most import from each other or from utilities already converted in Milestone 1.

### Pattern per model

Example — `BaseModel.js`:

```js
export default class BaseModel {
  constructor(definition, data) {
    this._definition = definition;
    if (data) Object.assign(this, data);
  }
}
```

Becomes `BaseModel.ts`:

```ts
export interface ModelDefinition {
  default: Record<string, unknown>;
  fields: string[];
  [k: string]: unknown;
}

export default class BaseModel<T extends Record<string, unknown> = Record<string, unknown>> {
  protected _definition: ModelDefinition;
  constructor(definition: ModelDefinition, data?: Partial<T>) {
    this._definition = definition;
    if (data) Object.assign(this, data);
  }
}
```

Subclasses (e.g., `Project.ts`):

```ts
import BaseModel from "./BaseModel";

export interface ProjectData {
  projectID: string;
  name: string;
  description: string | null;
  creation_time: string;
  owner: string;
}

export default class Project extends BaseModel<ProjectData> implements ProjectData {
  projectID!: string;
  name!: string;
  description!: string | null;
  creation_time!: string;
  owner!: string;

  constructor(data?: Partial<ProjectData>) {
    super({ default: {}, fields: ["projectID", "name", "description", "creation_time", "owner"] }, data);
  }
}
```

### Steps

- [ ] **Step 1: Enumerate model files**

```bash
find django_airavata/apps/api/static/django_airavata_api/js/models -name '*.js' -not -path '*/dist/*' | sort
```

- [ ] **Step 2: Convert `BaseModel.js` first (it's the root of the hierarchy)**

See pattern above. `git mv BaseModel.js BaseModel.ts`; add types.

- [ ] **Step 3: Convert leaf models (no imports from other models)**

Identify via grep: `grep -rln "from '\./" django_airavata/apps/api/static/django_airavata_api/js/models/*.js` — files without this pattern have no internal model imports and are safe to convert next.

- [ ] **Step 4: Convert remaining models in topological order**

For each remaining model:
1. Confirm every import target is already `.ts`.
2. `git mv Model.js Model.ts`.
3. Add type annotations + `interface ModelData` for the data shape.
4. Update imports in consumers to drop `.js`.

- [ ] **Step 5: Run typecheck**

```bash
npm run typecheck 2>&1 | tail -20
```
Expected: exit 0.

- [ ] **Step 6: Build + lint + tests + manifest parity**

Same gauntlet as Milestone 1 Step 5-6.

- [ ] **Step 7: Checkpoint commit**

```bash
git add -A
git commit -m "wip(track-a): API models .js → .ts (86 files)"
git log --oneline -3
```

---

## Task 3 — Milestone 3: Pinia scaffolding

**Goal:** Create the 3 new Pinia stores in `common/js/stores/`. Vuex stores remain untouched this milestone — new Pinia stores coexist alongside. Consumers still use `mapGetters`/`mapActions` until Milestone 4.

### Steps

- [ ] **Step 1: Add `pinia` to package.json files**

Edit `django_airavata/static/common/package.json` — add to `dependencies`:
```json
"pinia": "^2.1.0",
```

Edit each consuming workspace's `package.json` (`auth`, `admin`, `workspace`) — add same line.

Run `npm install 2>&1 | tail -3`.

- [ ] **Step 2: Create `common/js/stores/user.ts`**

See spec Section 2.2 for the full `useUserStore` implementation. Write it verbatim at `django_airavata/static/common/js/stores/user.ts`.

Prereq: `django_airavata/static/common/js/types/user.ts` must exist with `User`, `ExtendedUserProfileField`, `ExtendedUserProfileValue` interfaces. If not, create them now based on the existing Vuex state shape in `auth/store/modules/userProfile.js`.

- [ ] **Step 3: Create `common/js/stores/experiment.ts`**

Consolidate `workspace/store/modules/view-experiment.js`. Read the existing module to understand state/getters/actions/mutations; port to `defineStore("experiment", () => { ... })`.

- [ ] **Step 4: Create `common/js/stores/webComponents.ts`**

Port `workspace/web-components/store.js` similarly.

- [ ] **Step 5: Register Pinia on each workspace's entry**

For each workspace with a Vue app (admin, auth, workspace, dataparsers), find the entry file (`entry-*.js`) or main bootstrap and add:

```ts
import { createPinia } from "pinia";
// ...
const pinia = createPinia();
app.use(pinia);
```

Where `app` is the Vue app instance created by `createApp(Component)`.

- [ ] **Step 6: Run typecheck + build + lint + tests**

Same gauntlet; all pass.

- [ ] **Step 7: Checkpoint commit**

```bash
git add -A
git commit -m "wip(track-a): Pinia scaffolding (new stores coexist with Vuex)"
```

---

## Task 4 — Milestone 4: Pinia switchover

**Goal:** Migrate every Vuex consumer to the Pinia stores. Delete Vuex store files. Remove `"vuex"` dep.

### Steps

- [ ] **Step 1: Enumerate Vuex consumers**

```bash
grep -rln "mapGetters\|mapActions\|mapMutations\|mapState" \
  django_airavata --include='*.vue' --include='*.js' --include='*.ts' \
  | grep -v node_modules | grep -v dist | sort > /tmp/td-a-vuex-consumers.txt
wc -l /tmp/td-a-vuex-consumers.txt
```

- [ ] **Step 2: Migrate each consumer**

For each file in `/tmp/td-a-vuex-consumers.txt`:

Replace:
```js
import { mapGetters, mapActions } from "vuex";
// ...
computed: {
  ...mapGetters("userProfile", ["user"]),
},
methods: {
  ...mapActions("userProfile", ["loadCurrentUser"]),
},
```

With:
```ts
import { storeToRefs } from "pinia";
import { useUserStore } from "django-airavata-common-ui/js/stores/user";

const userStore = useUserStore();
const { user } = storeToRefs(userStore);
// then invoke userStore.loadCurrentUser() where mapActions bound to `loadCurrentUser` was used
```

Note: many consumers are still Options API at this milestone (Vue `.vue` rewrites come in milestones 5-7). If a consumer is still Options API, adapt:

```js
// In Options API until Milestone 5/6/7:
import { useUserStore } from "django-airavata-common-ui/js/stores/user";

export default {
  setup() {
    const userStore = useUserStore();
    return { userStore };
  },
  computed: {
    user() { return this.userStore.user; },
  },
  methods: {
    async loadCurrentUser() { await this.userStore.loadCurrentUser(); },
  },
};
```

The `setup()` hook coexists with Options API — this is the standard Vue 3 bridging pattern.

- [ ] **Step 3: Delete Vuex store directories**

```bash
git rm -r django_airavata/apps/auth/static/django_airavata_auth/js/store
git rm -r django_airavata/apps/workspace/static/django_airavata_workspace/js/store
git rm django_airavata/apps/workspace/static/django_airavata_workspace/js/web-components/store.js
git rm -r django_airavata/apps/admin/static/django_airavata_admin/src/store
```

- [ ] **Step 4: Remove `"vuex"` from every package.json**

Edit each workspace's `package.json`; delete the `"vuex": "..."` line.

Run `npm install 2>&1 | tail -3`.

- [ ] **Step 5: Verify**

```bash
grep -rn "from ['\"]vuex['\"]\|require(['\"]vuex['\"])" \
  django_airavata --include='*.vue' --include='*.js' --include='*.ts' \
  | grep -v node_modules | grep -v dist
# Expected: empty.

grep -rn "mapGetters\|mapActions\|mapMutations\|mapState" \
  django_airavata --include='*.vue' --include='*.js' --include='*.ts' \
  | grep -v node_modules | grep -v dist
# Expected: empty.

grep -n '"vuex"' django_airavata/apps/*/package.json django_airavata/static/common/package.json
# Expected: empty.
```

- [ ] **Step 6: Full gauntlet**

```bash
npm run typecheck
npm run lint
npm run test
npm run build --workspaces --if-present
for app in admin auth dataparsers workspace; do
  python3 -c "
import json
pre = {k for k in open('/tmp/td-a-pre-$app-manifest-keys.txt').read().splitlines() if k and not k.startswith('_')}
post = {k for k in json.load(open('django_airavata/apps/$app/static/django_airavata_$app/dist/manifest.json')) if not k.startswith('_')}
assert pre == post
print('OK $app')
"
done
```
All exit 0; 4× OK parity.

- [ ] **Step 7: Checkpoint commit**

```bash
git add -A
git commit -m "wip(track-a): Pinia switchover — delete Vuex, migrate consumers"
```

---

## Task 5 — Milestone 5: common library `.vue` → `<script setup lang="ts">`

**Goal:** Rewrite all 35 `.vue` files in `django_airavata/static/common/js/components/` to Vue 3 Composition + TS. These are the most-imported components; rewriting them first means downstream consumer rewrites (in later milestones) see a fully-typed import boundary.

### Pattern

See spec Section 2.1 for the full Options API → `<script setup lang="ts">` transformation rules. Apply systematically.

### Steps

- [ ] **Step 1: Enumerate common/ .vue files**

```bash
find django_airavata/static/common/js -name '*.vue' -not -path '*/node_modules/*' -not -path '*/dist/*' | sort > /tmp/td-a-common-vue.txt
wc -l /tmp/td-a-common-vue.txt
```
Expected: 35 files.

- [ ] **Step 2: Rewrite each file**

Apply the transformation rules from spec Section 2.1 to every file. Work in batches of ~5-8 files between verifications. Don't rename files (keep `.vue` extension — only the `<script>` block changes).

Between batches, run `npm run typecheck && npm run lint` to catch drift.

- [ ] **Step 3: Add missing type definitions**

As each component is rewritten, it may reference types not yet defined. Add them to `django_airavata/static/common/js/types/*.ts` on demand. Each type file has one conceptual domain (e.g., `types/project.ts` for project shapes).

- [ ] **Step 4: Verify all 35 files converted**

```bash
find django_airavata/static/common/js -name '*.vue' -exec grep -L "<script setup" {} + | grep -v node_modules | grep -v dist
# Expected: empty (all 35 have <script setup>).
```

- [ ] **Step 5: Full gauntlet**

```bash
npm run typecheck
npm run lint
npm run test
npm run build --workspaces --if-present

# Parity
for app in admin auth dataparsers workspace; do
  python3 -c "
import json
pre = {k for k in open('/tmp/td-a-pre-$app-manifest-keys.txt').read().splitlines() if k and not k.startswith('_')}
post = {k for k in json.load(open('django_airavata/apps/$app/static/django_airavata_$app/dist/manifest.json')) if not k.startswith('_')}
assert pre == post
print('OK $app')
"
done

# Zero escape hatches
grep -rn '@ts-expect-error\|@ts-ignore' django_airavata tooling tests \
  --include='*.vue' --include='*.ts' --include='*.js' 2>/dev/null \
  | grep -v node_modules | grep -v dist
# Expected: empty.
```

- [ ] **Step 6: Checkpoint commit**

```bash
git add -A
git commit -m "wip(track-a): common library .vue → Composition + TS (35 files)"
```

---

## Task 6 — Milestone 6: auth + dataparsers `.vue`

**Goal:** Rewrite 14 `.vue` files across auth (8) + dataparsers (6) to `<script setup lang="ts">`.

### Steps

- [ ] **Step 1: Enumerate files**

```bash
find django_airavata/apps/auth django_airavata/apps/dataparsers \
  -name '*.vue' -not -path '*/node_modules/*' -not -path '*/dist/*' | sort
```
Expected: 14 files.

- [ ] **Step 2: Rewrite auth first (8 files)**

Most are Extended User Profile editors + the auth container. The consolidated `useUserStore` from Milestone 3 is used here. Apply spec Section 2.1 rules.

- [ ] **Step 3: Rewrite dataparsers (6 files)**

Same transformation pattern.

- [ ] **Step 4: Full gauntlet + zero-escape-hatch check**

Same commands as Milestone 5 Step 5.

- [ ] **Step 5: Checkpoint commit**

```bash
git add -A
git commit -m "wip(track-a): auth + dataparsers .vue → Composition + TS (14 files)"
```

---

## Task 7 — Milestone 7: admin + workspace `.vue` + re-enable ESLint rules

**Goal:** Rewrite 130 `.vue` files (admin: 40 + workspace: 90). Re-elevate Track C's demoted ESLint rules to `error` in `tooling/eslint.config.js`.

### Steps

- [ ] **Step 1: Enumerate files**

```bash
find django_airavata/apps/admin django_airavata/apps/workspace \
  -name '*.vue' -not -path '*/node_modules/*' -not -path '*/dist/*' | sort > /tmp/td-a-admin-workspace-vue.txt
wc -l /tmp/td-a-admin-workspace-vue.txt
```
Expected: 130.

- [ ] **Step 2: Rewrite in batches**

Work through the list in batches of ~10-15 files per dispatch. Apply spec Section 2.1 rules. Between batches, run `npm run typecheck && npm run lint` locally to prevent drift.

Workspace contains the most complex components (experiment editor, application editor, file upload). These may hit `@ts-expect-error` pressure — recall Q4-a (zero tolerance). When a blocker surfaces, escalate rather than silently accept.

- [ ] **Step 3: Re-elevate ESLint rules in `tooling/eslint.config.js`**

Open `tooling/eslint.config.js`. Change the Track C-demoted rules from `warn` back to `error`:

- `vue/require-explicit-emits`: `"warn"` → `"error"`
- `vue/require-default-prop`: `"warn"` → `"error"`
- `vue/require-prop-types`: `"warn"` → `"error"`
- `vue/order-in-components`: `"warn"` → `"error"`
- `vue/attributes-order`: `"warn"` → `"error"`
- `vue/first-attribute-linebreak`: `"warn"` → `"error"`
- `vue/component-definition-name-casing`: `"warn"` → `"error"`
- `vue/prop-name-casing`: `"warn"` → `"error"`
- `vue/no-deprecated-slot-attribute`: `"warn"` → `"error"`
- `vue/no-deprecated-slot-scope-attribute`: `"warn"` → `"error"`
- `vue/no-deprecated-delete-set`: `"warn"` → `"error"`
- `vue/no-deprecated-events-api`: `"warn"` → `"error"`
- `vue/no-deprecated-v-on-native-modifier`: `"warn"` → `"error"`

After re-elevation, run `npm run lint`. Fix any new errors — most should be obviated by `<script setup>` (no more `emits:[]` arrays, no `mapGetters`, no deprecated slot syntax), but a few may surface.

- [ ] **Step 4: Full gauntlet + zero-escape-hatch check**

```bash
# All 179 .vue use <script setup>.
TOTAL=$(find django_airavata -name '*.vue' -not -path '*/node_modules/*' -not -path '*/dist/*' | wc -l | tr -d ' ')
SETUP=$(grep -rl "<script setup" django_airavata --include='*.vue' | grep -v node_modules | grep -v dist | wc -l | tr -d ' ')
echo "setup=$SETUP total=$TOTAL"
test "$SETUP" = "$TOTAL"

# Zero Vue 2 residue.
grep -rnE "^\s*(destroyed|beforeDestroy)\s*\(|this\.\\\$set\(|this\.\\\$off\(" \
  django_airavata --include='*.vue' --include='*.js' --include='*.ts' \
  | grep -v node_modules | grep -v dist

# Zero escape hatches.
grep -rn '@ts-expect-error\|@ts-ignore' django_airavata common tooling tests \
  --include='*.vue' --include='*.ts' --include='*.js' 2>/dev/null \
  | grep -v node_modules | grep -v dist

# Zero warnings.
npm run lint 2>&1 | grep -c "warning"

# Gauntlet
npm run typecheck
npm run test
npm run build --workspaces --if-present

# Parity
for app in admin auth dataparsers workspace; do
  python3 -c "
import json
pre = {k for k in open('/tmp/td-a-pre-$app-manifest-keys.txt').read().splitlines() if k and not k.startswith('_')}
post = {k for k in json.load(open('django_airavata/apps/$app/static/django_airavata_$app/dist/manifest.json')) if not k.startswith('_')}
assert pre == post
print('OK $app')
"
done
```

All exit 0; all greps empty; setup == total; parity 4×.

- [ ] **Step 5: Checkpoint commit**

```bash
git add -A
git commit -m "wip(track-a): admin + workspace .vue → Composition + TS (130 files) + re-enable ESLint"
```

---

## Task 8 — Final gate checks

**Files:** none (verification only).

Run every check from the spec's "Done criteria" section exactly.

- [ ] **Step 1: Run the 13 gate checks inline**

Execute the full block from spec Section "Done criteria". If any fails, return to the appropriate milestone, fix, re-run.

```bash
# (The exact 13 checks from the spec — do not paraphrase.)
```

- [ ] **Step 2: Zero-escape-hatch final sweep**

```bash
grep -rn '@ts-expect-error\|@ts-ignore\|as any\b\|as unknown as' \
  django_airavata common tooling tests \
  --include='*.vue' --include='*.ts' --include='*.js' 2>/dev/null \
  | grep -v node_modules | grep -v dist | grep -v "^.*vitest-setup"
```
Expected: empty (the `vitest-setup.ts` `as unknown as` in Track Pre-A is allowed).

---

## Task 9 — Squash and merge

- [ ] **Step 1: Archive wip commits for future bisect**

```bash
mkdir -p docs/superpowers
git format-patch c17520fb0e..HEAD --stdout > docs/superpowers/track-a-wip-commits.patch
ls -la docs/superpowers/track-a-wip-commits.patch
```

- [ ] **Step 2: Verify wip chain**

```bash
git log --oneline c17520fb0e..HEAD
```
Expected: 7-8 `wip(track-a):` commits on top of the spec commit.

- [ ] **Step 3: Soft-reset to spec commit**

```bash
git reset --soft c17520fb0e
git diff --cached --stat | tail -5
```

- [ ] **Step 4: Create the squashed commit**

```bash
git commit -m "$(cat <<'EOF'
refactor(portal): Vue 3 Composition + TypeScript + Pinia

Track A of the portal modernization umbrella. The largest track by far —
~340 files touched:
- 179 .vue files rewritten to <script setup lang="ts">
- ~76 utility + entry .js files converted to .ts (leaves-first)
- 86 API model files in django-airavata-api converted to .ts
- 8 Vuex store modules removed; 3 domain-driven Pinia stores added at
  django_airavata/static/common/js/stores/ (user, experiment, webComponents)
- All mapGetters / mapMutations / mapActions / mapState call sites removed
- All Vue 2 residue removed (destroyed, beforeDestroy, this.$set, this.$off)
- Track C-demoted ESLint rules re-elevated to error (vue/require-explicit-emits,
  vue/require-default-prop, vue/require-prop-types, vue/order-in-components,
  and the Vue 2 deprecation family)
- Zero @ts-expect-error / @ts-ignore anywhere

Strict TS via Track C's tooling/tsconfig.base.json (strict:true, allowJs:false).
Leaves-first conversion order enforced by per-milestone `npm run typecheck` —
archived at docs/superpowers/track-a-wip-commits.patch for bisect reference.

Functional parity: manifest keys identical across all 4 Django apps;
Track Pre-A test harness stayed green throughout; pytest summary
unchanged (backend untouched).

Spec: docs/superpowers/specs/2026-04-22-track-a-vue-composition-ts-pinia-design.md
EOF
)"
```

- [ ] **Step 5: Add the wip patch archive**

```bash
git add docs/superpowers/track-a-wip-commits.patch
git commit -m "docs(track-a): archive wip commits for bisect reference"
```

- [ ] **Step 6: Push + merge to modernization**

```bash
git push -u origin track-a/vue-composition-ts-pinia
git checkout modernization
git pull origin modernization
git merge --no-ff track-a/vue-composition-ts-pinia -m "merge: Track A (Vue Composition + TS + Pinia)"
git push origin modernization
```

- [ ] **Step 7: Verify**

```bash
git log --oneline --merges -6
```
Expected: top merge is `merge: Track A (Vue Composition + TS + Pinia)`; all 5 track merges visible.

---

## Plan Self-Review

**Spec coverage:**

| Spec section | Plan task |
|---|---|
| Scope 1: 179 .vue → script setup lang=ts | Tasks 5 (common), 6 (auth+dataparsers), 7 (admin+workspace) |
| Scope 2: .js → .ts utilities + models | Tasks 1 (utilities), 2 (models) |
| Scope 3: Vuex → Pinia (3 domain stores) | Tasks 3 (scaffolding), 4 (switchover) |
| Scope 4: Vue 2 residue cleanup | Tasks 5-7 (rewrites naturally drop destroyed/beforeDestroy/$set/$off) |
| Scope 5: Zero @ts-expect-error | Per-milestone check (Tasks 1-7 Step N) + Task 8 final sweep |
| Baseline capture | Task 0 |
| Per-milestone integration check | Tasks 1-7 Steps 4-6 |
| Final gate checks (13 from spec) | Task 8 |
| Re-elevate demoted ESLint rules | Task 7 Step 3 |
| Squash + merge | Task 9 |
| Archive wip commits | Task 9 Step 1, 5 |

Every spec requirement maps to a task.

**Placeholder scan:** no TBD/TODO/FIXME. File-by-file enumeration for 179 .vue rewrites intentionally omitted — the plan documents the transformation pattern; per-milestone execution enumerates via `find`. This is not a placeholder; it's batched work.

**Type consistency:** branch `track-a/vue-composition-ts-pinia`, Pinia store names (`useUserStore`, `useExperimentStore`, `useWebComponentsStore`), `/tmp/td-a-pre-*` baseline paths, milestone numbers, spec commit `c17520fb0e` all consistent across tasks.

---

## Execution handoff

Plan complete and saved to `airavata-django-portal/docs/superpowers/plans/2026-04-22-track-a-vue-composition-ts-pinia-plan.md`. Recommended execution: `superpowers:subagent-driven-development` with one dispatch per milestone (8 dispatches total — 0 for baseline, 1-7 for milestones, then inline gate checks + squash).

**Realistic note:** This plan is ambitious. My prior subagent dispatches on smaller rewrites (Track C ESLint fixes, Track Pre-A broken tests) hit context-exhaustion limits at ~100+ file changes per dispatch. Milestones 5-7 will likely need to be split into multiple dispatches (batches of ~15-25 files each). Expect per-milestone dispatch count:

- M1 (utilities): 1 dispatch
- M2 (models 86 files): 2-3 dispatches
- M3 (Pinia scaffolding): 1 dispatch
- M4 (switchover ~20 consumers): 1-2 dispatches
- M5 (common 35): 2 dispatches
- M6 (auth+dataparsers 14): 1 dispatch
- M7 (admin+workspace 130): 5-7 dispatches

~14-18 subagent dispatches total. Plan for re-dispatch on context exhaustion.
