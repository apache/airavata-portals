# Track B — Library Swaps Design

> Track B of the portal modernization umbrella. Umbrella spec:
> `docs/superpowers/specs/2026-04-21-portal-modernization-design.md`.

## Goal

Retire legacy JS libraries whose presence outlives their value, land
CodeMirror 6 behind a single shared component, and delete a 1.6 MB fossil
directory. Built on Track C's `tooling/` baseline. Deliberate user-visible
cosmetic changes are allowed in narrow, documented places (date ordinals);
functional regressions are not.

## Scope

One squashed commit on `track-b/library-swaps`.

### 1. `moment` → native `Intl`

All 9 portal call sites use only 4 patterns (`.fromNow()`, `.format("lll")`,
`.format("MMM Do YYYY")`, `.format("YYYY-MM-DD")`) plus one UTC variant.
Swap for `Intl.RelativeTimeFormat` + `Intl.DateTimeFormat` via a shared
helper at `django_airavata/static/common/js/utils/dates.js`.

**Cosmetic change (accepted):** "Apr 21st 2026" becomes "Apr 21, 2026". The
ordinal suffix ("st/nd/rd/th") is not supported by `Intl.DateTimeFormat`
without extra work, and only appears in 2 admin-statistics sites. Users who
rely on the ordinal get a flat number; the date remains unambiguous.

Remove `moment` from `django_airavata/apps/workspace/package.json` and from
the root `package.json` dependencies block.

Call sites to migrate (per exploration on modernization):

| File | Current | Replace with |
|---|---|---|
| `common/js/components/SidebarFeedItem.vue` | `moment(ts).fromNow()` | `relativeTime(ts)` |
| `workspace/.../project/ProjectListItem.vue` | `moment(dt).fromNow()` | `relativeTime(dt)` |
| `workspace/.../experiment/ExperimentSummary.vue` | `.fromNow()` × 3 | `relativeTime(x)` |
| `workspace/.../ExperimentListContainer.vue` | `.fromNow()` | `relativeTime(x)` |
| `workspace/.../ProjectOverviewContainer.vue` | `.fromNow()` × 2 | `relativeTime(x)` |
| `workspace/.../CreateExperimentContainer.vue` | `moment().format("lll")` | `formatShort(new Date())` |
| `admin/.../ExperimentStatisticsContainer.vue` | `.format("MMM Do YYYY")` + `.format("YYYY-MM-DD")` | `formatDate` + `formatIsoDate` |
| `admin/.../ExperimentDetailsView.vue` | `.fromNow()` × 3 | `relativeTime(x)` |
| `admin/.../NoticeEditor.vue` | `moment().format()` + `.utc().format()` × 2 | `formatShort` + `formatUtc` |

### 2. CodeMirror 5 → 6 behind `<CodeEditor>`

Build `django_airavata/static/common/js/components/CodeEditor.vue` wrapping
CodeMirror 6.

Props (Options API, consistent with the rest of the Vue 2-era codebase
until Track A rewrites it):

| Prop | Type | Default | Notes |
|---|---|---|---|
| `modelValue` | String | `""` | Two-way via `v-model`. |
| `language` | String | `null` | `"javascript"` / `"python"` / `"markdown"` / `null` (plaintext). Extensible. |
| `theme` | String | `"default"` | `"default"` / `"dark"` (ports the abcdef theme). |
| `readOnly` | Boolean | `false` | Disables editing; greys background. |
| `lineNumbers` | Boolean | `true` | Shows line gutter. |

Emits: `update:modelValue` (Vue 3 `v-model` contract).

The three historical "consumers" break down as:

- `workspace/.../storage-edit/UserStorageTextEditViewer.vue` — **real JS
  consumer**. Migrates to `<CodeEditor v-model=... :line-numbers=true>`.
- `workspace/.../web-components/input-editors/MultiFileInputEditor.vue`
  and `.../FileInputEditor.vue` — **CSS-only consumers**. Their
  `@import "~codemirror/..."` lines are dropped. If they ever need
  syntax-highlighted preview they adopt `<CodeEditor readOnly>`.

npm deps installed in `django_airavata/apps/workspace/package.json`:
- `@codemirror/state`, `@codemirror/view`, `@codemirror/commands`
- `@codemirror/lang-javascript`, `@codemirror/lang-python`,
  `@codemirror/lang-markdown`
- `@codemirror/theme-one-dark`

Deps removed: `codemirror` (5.x).

### 3. Delete `django_airavata/static/bootstrap-4.0.0-beta/`

Verification procedure (must pass before deletion):

```bash
grep -rln "bootstrap-4.0.0-beta" django_airavata \
  --include='*.py' --include='*.html' --include='*.vue' \
  --include='*.js' --include='*.ts' --include='*.scss' --include='*.css' \
  --include='*.json' --include='*.yaml' --include='*.yml' \
  | grep -v node_modules | grep -v dist
```
Expected: empty. If any reference is found, investigate before deleting.

Removes 1.6 MB from the tree. No replacement needed — the portal runs on
the Bootstrap shipped via BootstrapVue.

### 4. `vue-slider-component` stays on `4.1.0-beta.7`

Documented deviation from the umbrella's "off-beta" requirement.
Rationale: `4.1.x` is the only Vue 3-compatible line and never shipped
stable; `3.2.24` (latest stable) is Vue 2 only. PrimeVue / Radix would
require a second component library alongside BootstrapVue — a Track A
decision.

Edit `django_airavata/apps/workspace/package.json`:

```json
"vue-slider-component": "4.1.0-beta.7"  // Vue 3 support only on 4.x betas; 4.x never reached stable. Revisit if Track A adopts a new component library.
```

### 5. lodash removal (inline `_.debounce`)

Both call sites inline a small closure:

```js
// AutocompleteInputEditor.vue — searchChanged
searchChanged: (function () {
  let t;
  return function (newValue) {
    clearTimeout(t);
    t = setTimeout(() => {
      // original searchChanged body
    }, 300);
  };
})(),
```

```js
// ExperimentEditor.vue — calculateQueueSettings
// same pattern, async body preserved.
```

Delete `import _ from "lodash";` from both files. Drop `lodash` from
`django_airavata/apps/workspace/package.json`.

## Out of scope

- Any Composition API / TypeScript rewrite (Track A).
- PrimeVue / alternative component library adoption (Track A).
- BootstrapVue version change (not urgent).
- Any server-side work.

## Design decisions

| # | Decision | Alternatives |
|---|---|---|
| Q1 | Build `<CodeEditor>` component; migrate only the one real JS consumer | Retrofit all 3 "consumers" as umbrella said; replace CodeMirror with textarea + highlight.js |
| Q2 | Stay on `vue-slider-component@4.1.0-beta.7` with rationale | Hand-roll slider wrapping `<input type="range">`; bring in PrimeVue |
| Q3 | Native `Intl` + 5-function helper; no date-fns dep | Direct date-fns edits; shared helper wrapping date-fns |
| Q4 | Inline `_.debounce` logic at 2 call sites | Shared `debounce.js` helper; third-party `just-debounce-it` |
| Q5 | One squashed commit | 4 commits by swap; 5 commits by individual item |

## New code artifacts

### `django_airavata/static/common/js/utils/dates.js`

```js
const EN = "en-US";
const UNITS = [
  { limit: 60, unit: "second", div: 1 },
  { limit: 3600, unit: "minute", div: 60 },
  { limit: 86400, unit: "hour", div: 3600 },
  { limit: 2592000, unit: "day", div: 86400 },
  { limit: 31536000, unit: "month", div: 2592000 },
  { limit: Infinity, unit: "year", div: 31536000 },
];

export function relativeTime(date, now = new Date()) {
  const deltaSec = (new Date(date).getTime() - now.getTime()) / 1000;
  const abs = Math.abs(deltaSec);
  const u = UNITS.find((u) => abs < u.limit) ?? UNITS[UNITS.length - 1];
  const value = Math.round(deltaSec / u.div);
  return new Intl.RelativeTimeFormat(EN, { numeric: "auto" }).format(value, u.unit);
}

export function formatShort(date) {
  return new Intl.DateTimeFormat(EN, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(date));
}

export function formatDate(date) {
  return new Intl.DateTimeFormat(EN, {
    month: "short",
    day: "numeric",
    year: "numeric",
  }).format(new Date(date));
}

export function formatIsoDate(date) {
  return new Date(date).toISOString().slice(0, 10);
}

export function formatUtc(date) {
  return new Date(date).toISOString().replace(/\.\d{3}Z$/, "Z");
}
```

### `django_airavata/static/common/js/components/CodeEditor.vue`

```vue
<template>
  <div
    ref="host"
    class="code-editor"
    :class="{ 'code-editor--readonly': readOnly }"
  />
</template>

<script>
import { EditorView, keymap, lineNumbers as cmLineNumbers } from "@codemirror/view";
import { EditorState } from "@codemirror/state";
import { defaultKeymap, history, historyKeymap } from "@codemirror/commands";
import { javascript } from "@codemirror/lang-javascript";
import { python } from "@codemirror/lang-python";
import { markdown } from "@codemirror/lang-markdown";
import { oneDark } from "@codemirror/theme-one-dark";

const LANGS = { javascript, python, markdown };

export default {
  name: "CodeEditor",
  props: {
    modelValue: { type: String, default: "" },
    language: { type: String, default: null },
    theme: { type: String, default: "default" },
    readOnly: { type: Boolean, default: false },
    lineNumbers: { type: Boolean, default: true },
  },
  emits: ["update:modelValue"],
  data() {
    return { view: null };
  },
  mounted() {
    const exts = [history(), keymap.of([...defaultKeymap, ...historyKeymap])];
    if (this.lineNumbers) exts.push(cmLineNumbers());
    if (this.language && LANGS[this.language]) exts.push(LANGS[this.language]());
    if (this.theme === "dark") exts.push(oneDark);
    if (this.readOnly) exts.push(EditorState.readOnly.of(true));
    exts.push(
      EditorView.updateListener.of((u) => {
        if (u.docChanged) this.$emit("update:modelValue", u.state.doc.toString());
      }),
    );
    this.view = new EditorView({
      doc: this.modelValue,
      extensions: exts,
      parent: this.$refs.host,
    });
  },
  beforeUnmount() {
    this.view?.destroy();
    this.view = null;
  },
  watch: {
    modelValue(next) {
      const current = this.view?.state.doc.toString();
      if (next !== current) {
        this.view.dispatch({
          changes: { from: 0, to: current.length, insert: next },
        });
      }
    },
  },
};
</script>

<style scoped>
.code-editor {
  border: 1px solid var(--bs-border-color, #ced4da);
  border-radius: 4px;
}
.code-editor--readonly {
  background: #f8f9fa;
}
</style>
```

## Testing protocol

### Layer 1 — Static + build

```bash
npm run lint
npm run typecheck
npm run build --workspaces --if-present

# Manifest logical-entry parity (filters `_`-prefixed auto-chunks).
for app in admin auth dataparsers workspace; do
  python3 -c "
import json
pre = {k for k in open('/tmp/td-b-pre-$app-manifest-keys.txt').read().splitlines() if k and not k.startswith('_')}
post = {k for k in json.load(open('django_airavata/apps/$app/static/django_airavata_$app/dist/manifest.json')) if not k.startswith('_')}
assert pre == post, f'$app manifest drift: +{post-pre} -{pre-post}'
print('OK $app')
"
done
```

### Layer 2 — pytest

```bash
uv run pytest -q
```
Expected: identical summary to modernization baseline.

### Layer 3 — Bundle size diff

```bash
# Captured pre-Track-B (Task 1 of the plan):
cat /tmp/td-b-pre-workspace-size.txt
# ...

# Post-Track-B:
for app in admin auth dataparsers workspace; do
  pre=$(cat /tmp/td-b-pre-$app-size.txt | awk '{print $1}')
  post=$(du -sh django_airavata/apps/$app/static/django_airavata_$app/dist/assets | awk '{print $1}')
  echo "$app: $pre → $post"
done
```
Expected: workspace + admin shrink (moment ~67KB gzipped; CM5 + themes ~200KB gzipped). Growth is a red flag.

### Layer 4 — Manual smoke (operator-run)

1. `/workspace/experiments` — experiment-creation time renders "X minutes/hours ago".
2. `/workspace/projects` — project-creation time renders similarly.
3. `/admin/statistics` — from/to date display reads "Apr 21, 2026" (no ordinal; expected cosmetic change).
4. `/admin/notices` — create a notice with future expiration; UTC time correct.
5. `/workspace/storage` — text file editor loads, typing + save round-trips.
6. experiment editor with range-input parameter — slider renders + reports value.

Any regression → revert offending portion and retry.

## Done criteria (gate checks)

```bash
# 1. No moment imports.
grep -rn "from ['\"]moment['\"]\|require(['\"]moment['\"])" \
  django_airavata --include='*.vue' --include='*.js' --include='*.ts' \
  | grep -v node_modules | grep -v dist
# 2. moment dep gone from package.json files.
grep -n '"moment"' django_airavata/apps/workspace/package.json package.json
# 3. No CodeMirror 5 imports anywhere.
grep -rn "from ['\"]codemirror['\"]\|require(['\"]codemirror['\"])\|~codemirror/" \
  django_airavata --include='*.vue' --include='*.js' --include='*.ts' --include='*.scss' --include='*.css' \
  | grep -v node_modules | grep -v dist
grep -n '"codemirror"' django_airavata/apps/*/package.json django_airavata/static/common/package.json
# 4. Bootstrap 4 beta fossil gone.
test ! -d django_airavata/static/bootstrap-4.0.0-beta
find django_airavata -type d -name 'bootstrap-*-beta*' -not -path '*/node_modules/*'
# 5. No lodash imports.
grep -rn "from ['\"]lodash['\"]\|require(['\"]lodash['\"])" \
  django_airavata --include='*.vue' --include='*.js' --include='*.ts' \
  | grep -v node_modules | grep -v dist
grep -n '"lodash"' django_airavata/apps/*/package.json django_airavata/static/common/package.json
# 6. vue-slider pin has inline rationale.
grep 'vue-slider-component' django_airavata/apps/workspace/package.json
# 7. CodeEditor component exists; real consumer uses it.
test -f django_airavata/static/common/js/components/CodeEditor.vue
grep -n "CodeEditor" \
  django_airavata/apps/workspace/static/django_airavata_workspace/js/components/storage/storage-edit/UserStorageTextEditViewer.vue
# 8. Former CSS-only consumers no longer reference codemirror.
grep -n "codemirror" \
  django_airavata/apps/workspace/static/django_airavata_workspace/js/web-components/input-editors/MultiFileInputEditor.vue \
  django_airavata/apps/workspace/static/django_airavata_workspace/js/web-components/input-editors/FileInputEditor.vue
# 9. No date-fns dep introduced.
grep -n '"date-fns"\|"date-fns-tz"' \
  django_airavata/apps/*/package.json \
  django_airavata/static/common/package.json \
  package.json
# 10. Shared dates helper exists.
test -f django_airavata/static/common/js/utils/dates.js
# 11. CodeMirror 6 installed in package-lock.
python3 -c "
import json
lock = json.load(open('package-lock.json'))
cm6 = [k for k in lock.get('packages', {}) if k.startswith('node_modules/@codemirror/')]
assert len(cm6) >= 5, f'expected >= 5 @codemirror/* packages, got {len(cm6)}'
print(f'OK {len(cm6)}')
"
# 12. Every workspace builds.
npm run build --workspaces --if-present
# 13. Lint still passes.
npm run lint
# 14. Bundle size did not grow.
# (captured in Testing Layer 3)
```

Expected: 1, 2, 3, 5, 8, 9 empty; 4, 6, 7, 10, 11, 12, 13 OK.

## Risks and mitigations

| Risk | Mitigation |
|---|---|
| Intl.RelativeTimeFormat locale output differs from moment.fromNow() in subtle ways | Layer 4 manual smoke spot-checks; acceptable cosmetic drift documented |
| CodeMirror 6 bundle is larger than CodeMirror 5 due to more packages | Layer 3 bundle-size gate catches growth; if growth, narrow CM6 extensions |
| UserStorageTextEditViewer depends on subtle CM5 behavior not mirrored in the wrapper (cursor position, focus handling) | Layer 4 manual smoke; if regression, add missing props/events to `<CodeEditor>` before merging |
| `v-model` loop between CodeEditor and consumers | The `watch` in CodeEditor checks equality before dispatching — covered in spec |
| lodash removal from inline debounces has subtle timing differences | Debounce behavior is straightforward; side-by-side smoke test the "search" feature |
| Dropping the abcdef theme may surprise users | Layer 4 smoke check the editor styling; if pushback, add abcdef to `<CodeEditor>` themes |
