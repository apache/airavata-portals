# Track A — Vue Composition + TypeScript + Pinia Design

> Track A of the portal modernization umbrella. Umbrella spec:
> `docs/superpowers/specs/2026-04-21-portal-modernization-design.md`.

## Goal

Complete the Vue-2-era → Vue 3 Composition + TypeScript + Pinia rewrite on
`track-a/vue-composition-ts-pinia`, landing as one squashed commit on
`modernization`. The umbrella's largest track — 179 `.vue` files + 76+86
`.js` files + 8 Vuex stores.

## Scope

One squashed commit on `track-a/vue-composition-ts-pinia`.

### 1. 179 `.vue` files → `<script setup lang="ts">`

| Workspace | `.vue` count |
|---|---|
| common | 35 |
| admin | 40 |
| auth | 8 |
| dataparsers | 6 |
| workspace | 90 |

### 2. `.js` → `.ts` for type/model sources

- 86 API model files in `django_airavata/apps/api/static/django_airavata_api/js/models/`.
- 76 utility / store / entry `.js` files across workspaces. Convert those
  that define types, constants, or are imported into `.ts` / `.vue<script lang=ts>`.

Leaves-first order (per Q1-a) — driven by Track C's `allowJs: false` in
`tooling/tsconfig.base.json`: once any file is `.ts`, its transitive import
closure must also be `.ts` for `vue-tsc` to pass.

### 3. Vuex → Pinia (domain-driven flattening, Q2-b)

Current Vuex layout:

```
django_airavata/apps/auth/static/django_airavata_auth/js/store/index.js
django_airavata/apps/auth/.../store/modules/userProfile.js
django_airavata/apps/auth/.../store/modules/extendedUserProfile.js
django_airavata/apps/workspace/static/django_airavata_workspace/js/store/index.js
django_airavata/apps/workspace/.../store/modules/view-experiment.js
django_airavata/apps/workspace/.../web-components/store.js      (standalone)
django_airavata/apps/admin/static/django_airavata_admin/src/store/index.js
django_airavata/apps/admin/.../store/modules/extendedUserProfile.js   (dup of auth's)
```

New Pinia layout under `django_airavata/static/common/js/stores/`:

```
common/js/stores/
├── user.ts             # userProfile + extendedUserProfile (combined)
├── experiment.ts       # view-experiment
└── webComponents.ts    # standalone workspace web-component state
```

All consumers (currently in auth, workspace, admin) import from
`django-airavata-common-ui/js/stores/...`. Old per-workspace `store/`
directories deleted at end. `"vuex"` removed from every `package.json`.

### 4. Vue 2 residue cleanup

- 2 `this.$set` call sites → direct assignment (Vue 3 reactivity handles
  this natively with `reactive` / `ref`).
- 2 `destroyed()` lifecycle → `onUnmounted()` equivalent in `<script setup>`.
- No `$off`/`beforeDestroy` remaining (cleanup from earlier in this session).

### 5. `@ts-expect-error` / `@ts-ignore`: zero at end (Q4-a)

Per-milestone and final-gate grep returns empty. Any blocker that would
require an escape hatch is escalated, not silently applied.

## Out of scope

- BootstrapVue → PrimeVue / alt component library (future track).
- New features, new routes, new business logic.
- Any user-facing behavioral change.
- Non-type-definitional `.js` in the api workspace (`index.js`, service
  factories, runtime bootstrap) — keep as `.js` unless a `.ts` consumer
  forces conversion.

## Design decisions

| # | Decision | Alternatives |
|---|---|---|
| Q1 | Leaves-first dependency order | Workspace-at-a-time; loosen `allowJs:true` temporarily |
| Q2 | Domain-driven Pinia flattening (3 stores in common) | Mirror Vuex modules 1:1; per-workspace single store |
| Q3 | One mega-squash commit at end | Weekly squash merges; preserved wip commits |
| Q4 | Zero-tolerance `@ts-expect-error` | Tracked grace period; unrestricted with final sweep |

## Development strategy

Single long-lived branch `track-a/vue-composition-ts-pinia` off `modernization`.
7 internal milestones, each a `wip(track-a):` checkpoint commit. Final
squash at end.

| # | Milestone | Rough LOC | Gate |
|---|---|---|---|
| 1 | Utility leaves `.js` → `.ts` | ~20 files | `npm run typecheck` exit 0 |
| 2 | API models `.js` → `.ts` | ~86 files | `npm run typecheck` exit 0 |
| 3 | Pinia scaffolding (new stores coexist with Vuex) | ~3 stores + integration wiring | All existing tests still pass |
| 4 | Pinia switchover (consumers migrate; Vuex deleted) | ~20 consumer files | `grep vuex` empty; tests pass |
| 5 | common library `.vue` → `<script setup lang=ts>` | 35 .vue | `npm run typecheck` + lint + build |
| 6 | auth + dataparsers `.vue` | 14 .vue | same gate |
| 7 | admin + workspace `.vue` | 130 .vue | same gate + re-enable ESLint rules Track C demoted |

## Conversion patterns

### Options API → `<script setup lang="ts">`

Example (ProjectListItem.vue):

**Before:**

```vue
<script>
import urls from "../../utils/urls";
import { relativeTime } from "django-airavata-common-ui/js/utils/dates.js";

export default {
  name: "ProjectListItem",
  props: {
    project: { type: Object, required: true },
  },
  computed: {
    ownerUsername() { return this.project.owner; },
    creationTime() { return relativeTime(this.project.creation_time); },
  },
  methods: {
    navigate() { window.location = urls.project(this.project.projectID); },
  },
};
</script>
```

**After:**

```vue
<script setup lang="ts">
import { computed } from "vue";
import urls from "../../utils/urls";
import { relativeTime } from "django-airavata-common-ui/js/utils/dates";
import type { Project } from "@/types/project";

const props = defineProps<{ project: Project }>();
defineEmits<{ delete: [Project] }>();

const ownerUsername = computed(() => props.project.owner);
const creationTime = computed(() => relativeTime(props.project.creation_time));

function navigate() {
  window.location.href = urls.project(props.project.projectID);
}
</script>
```

Transformation rules applied systematically:

| Options API | `<script setup lang="ts">` |
|---|---|
| `data() { return { x: 0 }; }` | `const x = ref(0);` |
| `computed: { y() { ... } }` | `const y = computed(() => ...);` |
| `methods: { m() { ... } }` | `function m() { ... }` |
| `props: { p: { type: X, required: true } }` | `const props = defineProps<{ p: X }>();` |
| `emits: ["e"]` | `defineEmits<{ e: [PayloadType] }>();` |
| `mounted() { ... }` | `onMounted(() => { ... });` |
| `beforeUnmount() { ... }` | `onBeforeUnmount(() => { ... });` |
| `destroyed() { ... }` | `onUnmounted(() => { ... });` |
| `mapGetters("s", ["x"])` | `const s = useStore(); const x = computed(() => s.x);` |
| `this.$emit("e", p)` | `emit("e", p);` |
| `this.$set(o, k, v)` | `o[k] = v;` (Vue 3 native reactivity) |
| `this.prop` (inside method) | `props.prop` |
| `this.localVar` (inside method) | `localVar.value` (refs) / `localVar` (non-refs) |

### Pinia store pattern

```ts
// django_airavata/static/common/js/stores/user.ts
import { defineStore } from "pinia";
import { ref, computed } from "vue";
import { services } from "django-airavata-api";
import type { User, ExtendedUserProfileField, ExtendedUserProfileValue } from "@/types/user";

export const useUserStore = defineStore("user", () => {
  const user = ref<User | null>(null);
  const extendedFields = ref<ExtendedUserProfileField[]>([]);
  const extendedValues = ref<ExtendedUserProfileValue[]>([]);

  const hasExtendedUserProfileFields = computed(() => extendedFields.value.length > 0);

  async function loadCurrentUser() {
    user.value = await services.UserService.current();
  }

  async function updateUser() {
    if (!user.value) return;
    user.value = await services.UserService.update({ lookup: user.value.id, data: user.value });
  }

  async function verifyEmailChange(code: string) {
    if (!user.value) return;
    user.value = await services.UserService.verifyEmailChange({ lookup: user.value.id, data: { code } });
  }

  async function resendEmailVerification() {
    if (!user.value) return;
    await services.UserService.resendEmailVerification({ lookup: user.value.id });
  }

  async function loadExtendedUserProfileFields() {
    extendedFields.value = await services.ExtendedUserProfileFieldService.list();
  }

  async function loadExtendedUserProfileValues() {
    extendedValues.value = await services.ExtendedUserProfileValueService.list();
  }

  async function saveExtendedUserProfileValues() {
    await services.ExtendedUserProfileValueService.saveBatch({ data: extendedValues.value });
  }

  return {
    user, extendedFields, extendedValues,
    hasExtendedUserProfileFields,
    loadCurrentUser, updateUser, verifyEmailChange, resendEmailVerification,
    loadExtendedUserProfileFields, loadExtendedUserProfileValues, saveExtendedUserProfileValues,
  };
});
```

### Consumer migration example

```vue
<script setup lang="ts">
import { onMounted } from "vue";
import { storeToRefs } from "pinia";
import { useUserStore } from "django-airavata-common-ui/js/stores/user";

const store = useUserStore();
const { user, extendedFields, hasExtendedUserProfileFields } = storeToRefs(store);

onMounted(async () => {
  await store.loadCurrentUser();
  await store.loadExtendedUserProfileFields();
});
</script>
```

### `.js` → `.ts` leaf conversion rules

| Pattern | Transform |
|---|---|
| `function foo(x) { ... }` | `function foo(x: X): R { ... }` — infer from call sites |
| `export default class Foo { ... }` | Add typed fields + method signatures |
| `export const C = ...` | Let TS infer or annotate explicitly |
| JSDoc `@param`/`@returns` | Promote to TS types; delete JSDoc |

## Testing protocol

### 3.1 — Baseline capture (Task 1 of the plan)

On `track-a/vue-composition-ts-pinia` HEAD before any rewrite:

```bash
npm run build --workspaces --if-present
for app in admin auth dataparsers workspace; do
  python3 -c "
import json
keys = sorted(k for k in json.load(open('django_airavata/apps/$app/static/django_airavata_$app/dist/manifest.json')) if not k.startswith('_'))
open('/tmp/td-a-pre-$app-manifest-keys.txt', 'w').write('\n'.join(keys) + '\n')
"
  du -s django_airavata/apps/$app/static/django_airavata_$app/dist/assets \
    > /tmp/td-a-pre-$app-size.txt
done
npm run test 2>&1 | tail -5 > /tmp/td-a-pre-test-summary.txt
```

### 3.2 — Per-milestone integration checks

After each of the 7 wip milestones:

```bash
npm run typecheck          # vue-tsc + strict: leaves-first enforcer
npm run lint               # ESLint 9 (Track C's demoted rules stay warn until milestone 7)
npm run test               # Vitest; count cannot decay
npm run build --workspaces --if-present   # dist still builds

# Manifest parity
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

If any check fails, stop. Fix before next milestone.

### 3.3 — Rollback posture

Pre-squash: `git reset --soft HEAD~1` undoes one milestone.
Post-squash, pre-merge: `git reset --soft <spec-commit>`; re-squash.
Post-merge on `modernization`: `git revert -m 1 <track-a-merge-commit>`.

## Done criteria (gate checks)

Umbrella plan's Task 5 Step 5 runs these exactly:

```bash
# 1. Every .vue uses <script setup>.
TOTAL=$(find django_airavata -name '*.vue' -not -path '*/node_modules/*' -not -path '*/dist/*' | wc -l | tr -d ' ')
SETUP=$(grep -rl "<script setup" django_airavata --include='*.vue' | grep -v node_modules | grep -v dist | wc -l | tr -d ' ')
test "$SETUP" = "$TOTAL"

# 2. Zero Vue 2 residues.
grep -rnE "^\s*(destroyed|beforeDestroy)\s*\(|this\.\\\$set\(|this\.\\\$off\(" \
  django_airavata --include='*.vue' --include='*.js' --include='*.ts' \
  | grep -v node_modules | grep -v dist

# 3. Zero Vuex map*.
grep -rnE 'mapGetters|mapMutations|mapActions|mapState' \
  django_airavata --include='*.vue' --include='*.js' --include='*.ts' \
  | grep -v node_modules | grep -v dist

# 4. No vuex imports or deps.
grep -rn "from ['\"]vuex['\"]\|require(['\"]vuex['\"])" \
  django_airavata --include='*.vue' --include='*.js' --include='*.ts' \
  | grep -v node_modules | grep -v dist
grep -n '"vuex"' django_airavata/apps/*/package.json django_airavata/static/common/package.json

# 5. Pinia is installed where stores are consumed.
grep -n '"pinia"' django_airavata/apps/*/package.json django_airavata/static/common/package.json
# Expected: common + every consuming workspace.

# 6. vue-tsc strict passes.
npm run typecheck

# 7. No @ts-expect-error / @ts-ignore.
grep -rn '@ts-expect-error\|@ts-ignore' django_airavata common tooling tests \
  --include='*.vue' --include='*.ts' --include='*.js' 2>/dev/null \
  | grep -v node_modules | grep -v dist

# 8. Tests green; count did not decay.
npm run test

# 9. Playwright spec listable.
npx playwright test --config=tooling/playwright.config.ts --list

# 10. Every workspace builds; manifest parity.
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

# 11. ESLint warns (Track C's demoted rules) now zero — re-elevate in
#     tooling/eslint.config.js during milestone 7.
npm run lint 2>&1 | grep "warn" | wc -l

# 12. Python side unchanged (sanity check).
uv run ruff check .
uv run ty check .
uv run pytest -q

# 13. Old Vuex store/ directories deleted.
find django_airavata -type d -name 'store' -not -path '*/node_modules/*' -not -path '*/dist/*'
# Expected: empty or only the new common/js/stores/.
```

## Risks and mitigations

| Risk | Mitigation |
|---|---|
| Subagent context exhaustion on dozens-of-files rewrites | 7 milestones; each is its own dispatch; re-dispatch on exhaustion |
| `allowJs: false` surfaces ordering violation late in a milestone | Per-milestone `npm run typecheck` gate; convert the surfaced .js leaf first |
| Pinia consolidation drops state a component relied on | Scaffolding + switchover as separate milestones; smoke-test each consumer |
| Zero-`@ts-expect-error` forces out-of-scope refactor | Escalate + brainstorm; no silent `any` |
| Test count shrinks silently | Per-milestone `npm run test` count check |
| Final mega-squash loses wip bisect context | `git format-patch` archive to `docs/superpowers/` before squash |
| Component with complex Options API doesn't cleanly map | `<script lang="ts">` (not setup) allowed for up to 5 files; explicit list in spec / final commit message |
