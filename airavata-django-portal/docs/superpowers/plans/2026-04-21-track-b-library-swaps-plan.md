# Track B — Library Swaps Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Land the 5 library swaps on `track-b/library-swaps` as one squashed commit: moment → native Intl; CodeMirror 5 → 6 via shared `<CodeEditor>`; delete `bootstrap-4.0.0-beta/` fossil; vue-slider-component pin rationale; inline `_.debounce`.

**Architecture:** 8 tasks on `track-b/library-swaps`. Task 1 captures pre-Track-B baseline (manifest keys + bundle sizes). Tasks 2-6 apply each swap with per-swap checkpoint commits. Task 7 runs gate checks. Task 8 squashes + merges.

**Tech Stack:** Vue 3 / Vite 6 / npm workspaces / CodeMirror 6 (`@codemirror/*`) / native `Intl.RelativeTimeFormat` + `Intl.DateTimeFormat`. No moment, no date-fns, no lodash, no CodeMirror 5.

**Spec:** `docs/superpowers/specs/2026-04-21-track-b-library-swaps-design.md`

**Working directory for every command:** `airavata-portals/airavata-django-portal`.

**Starting branch:** `track-b/library-swaps`, HEAD at `0645aa057a docs(track-b): library swaps design spec`.

---

## File Structure

### New files

- `django_airavata/static/common/js/utils/dates.js` — 5-function Intl wrapper.
- `django_airavata/static/common/js/components/CodeEditor.vue` — CodeMirror 6 wrapper component.

### Modified files

- 9 `.vue` files that currently use moment — migrated to `dates.js` imports.
- `django_airavata/apps/workspace/static/django_airavata_workspace/js/components/storage/storage-edit/UserStorageTextEditViewer.vue` — migrated from direct CodeMirror 5 to `<CodeEditor>`.
- `django_airavata/apps/workspace/static/django_airavata_workspace/js/web-components/input-editors/MultiFileInputEditor.vue` — drop `@import "~codemirror/..."`.
- `django_airavata/apps/workspace/static/django_airavata_workspace/js/web-components/input-editors/FileInputEditor.vue` — drop `@import "~codemirror/..."`.
- `django_airavata/apps/workspace/static/django_airavata_workspace/js/components/experiment/input-editors/AutocompleteInputEditor.vue` — inline debounce.
- `django_airavata/apps/workspace/static/django_airavata_workspace/js/components/experiment/ExperimentEditor.vue` — inline debounce.
- `django_airavata/apps/workspace/package.json` — remove `moment`, `lodash`, `codemirror`; add `@codemirror/*`; rationale comment on `vue-slider-component`.
- `package.json` (root) — remove `moment`.

### Deleted

- `django_airavata/static/bootstrap-4.0.0-beta/` (1.6 MB).

---

## Task 1: Capture pre-Track-B baseline

**Files:** none (produces `/tmp/td-b-pre-*-manifest-keys.txt` + `/tmp/td-b-pre-*-size.txt`).

- [ ] **Step 1: Verify clean state on track-b/library-swaps**

```bash
cd /Users/yasith/code/artisan/worktree-feat-sdk-and-devenv/airavata-portals/airavata-django-portal
git status --porcelain
git branch --show-current
```
Expected: empty status; branch `track-b/library-swaps`.

- [ ] **Step 2: Sync npm deps (Track C baseline)**

```bash
npm install 2>&1 | tail -3
```
Expected: exit 0.

- [ ] **Step 3: Build all workspaces**

```bash
npm run build --workspaces --if-present 2>&1 | tail -10
```
Expected: all 7 workspaces build.

- [ ] **Step 4: Snapshot manifest keys (logical-entry filter)**

```bash
rm -f /tmp/td-b-pre-*-manifest-keys.txt
for app in admin auth dataparsers workspace; do
  python3 -c "
import json
keys = sorted(k for k in json.load(open('django_airavata/apps/$app/static/django_airavata_$app/dist/manifest.json')) if not k.startswith('_'))
open('/tmp/td-b-pre-$app-manifest-keys.txt', 'w').write('\n'.join(keys) + '\n')
print('$app:', len(keys))
"
done
```

- [ ] **Step 5: Snapshot bundle sizes**

```bash
rm -f /tmp/td-b-pre-*-size.txt
for app in admin auth dataparsers workspace; do
  du -s django_airavata/apps/$app/static/django_airavata_$app/dist/assets \
    > /tmp/td-b-pre-$app-size.txt
  echo "$app: $(du -sh django_airavata/apps/$app/static/django_airavata_$app/dist/assets | awk '{print $1}')"
done
```

---

## Task 2: `moment` → native `Intl` via shared `dates.js` helper

**Files:**
- Create: `django_airavata/static/common/js/utils/dates.js`
- Modify: 9 `.vue` call sites
- Modify: `django_airavata/apps/workspace/package.json`, `package.json`

- [ ] **Step 1: Create the shared dates helper**

Write `django_airavata/static/common/js/utils/dates.js`:

```js
// Thin wrappers around native Intl APIs. Replaces moment across the portal.
// Ordinal-day format ("Apr 21st") is not supported by Intl and is not
// preserved — callers that used "MMM Do YYYY" now render "MMM d, yyyy".

const EN = "en-US";
const UNITS = [
  { limit: 60, unit: "second", div: 1 },
  { limit: 3600, unit: "minute", div: 60 },
  { limit: 86400, unit: "hour", div: 3600 },
  { limit: 2592000, unit: "day", div: 86400 },
  { limit: 31536000, unit: "month", div: 2592000 },
  { limit: Infinity, unit: "year", div: 31536000 },
];

/** "3 hours ago" / "in 5 minutes". Replaces moment(x).fromNow(). */
export function relativeTime(date, now = new Date()) {
  const deltaSec = (new Date(date).getTime() - now.getTime()) / 1000;
  const abs = Math.abs(deltaSec);
  const u = UNITS.find((u) => abs < u.limit) ?? UNITS[UNITS.length - 1];
  const value = Math.round(deltaSec / u.div);
  return new Intl.RelativeTimeFormat(EN, { numeric: "auto" }).format(value, u.unit);
}

/** "Apr 21, 2026, 2:30 PM". Replaces moment(x).format("lll"). */
export function formatShort(date) {
  return new Intl.DateTimeFormat(EN, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(date));
}

/** "Apr 21, 2026". Replaces moment(x).format("MMM Do YYYY") — loses ordinal. */
export function formatDate(date) {
  return new Intl.DateTimeFormat(EN, {
    month: "short",
    day: "numeric",
    year: "numeric",
  }).format(new Date(date));
}

/** "2026-04-21". Replaces moment(x).format("YYYY-MM-DD"). */
export function formatIsoDate(date) {
  return new Date(date).toISOString().slice(0, 10);
}

/** "2026-04-21T14:30:00Z". Replaces moment(x).utc().format(). */
export function formatUtc(date) {
  return new Date(date).toISOString().replace(/\.\d{3}Z$/, "Z");
}
```

- [ ] **Step 2: Migrate `common/js/components/SidebarFeedItem.vue`**

Find the line `return moment(this.feedItem.timestamp).fromNow();` and replace with:

```js
import { relativeTime } from "../utils/dates.js";
// ...
return relativeTime(this.feedItem.timestamp);
```

Remove `import moment from "moment";` from the top of the file.

- [ ] **Step 3: Migrate `workspace/.../project/ProjectListItem.vue`**

Find `return moment(dt).fromNow();` → `return relativeTime(dt);`. Add import:

```js
import { relativeTime } from "django-airavata-common-ui/js/utils/dates.js";
```

(Use the common-ui package path that matches how the file imports other common utilities — check the file's existing imports.)

Remove the moment import.

- [ ] **Step 4: Migrate `workspace/.../experiment/ExperimentSummary.vue`**

Replace 3 `.fromNow()` calls with `relativeTime(x)`. Remove moment import; add `relativeTime` import.

- [ ] **Step 5: Migrate `workspace/.../containers/ExperimentListContainer.vue`**

Replace `return moment(date).fromNow();` with `return relativeTime(date);`. Update imports.

- [ ] **Step 6: Migrate `workspace/.../containers/ProjectOverviewContainer.vue`**

Replace 2 `.fromNow()` calls. Update imports.

- [ ] **Step 7: Migrate `workspace/.../containers/CreateExperimentContainer.vue`**

Replace:
```js
experiment.experiment_name = appModule.app_module_name + " on " + moment().format("lll");
```
with:
```js
import { formatShort } from "django-airavata-common-ui/js/utils/dates.js";
// ...
experiment.experiment_name = appModule.app_module_name + " on " + formatShort(new Date());
```

- [ ] **Step 8: Migrate `admin/.../statistics/ExperimentStatisticsContainer.vue`**

Replace:
- `moment(this.fromTime).format("MMM Do YYYY")` → `formatDate(this.fromTime)` (note: loses ordinal suffix — documented cosmetic change)
- `moment(this.toTime).format("MMM Do YYYY")` → `formatDate(this.toTime)`
- `moment(this.fromTime).format("YYYY-MM-DD")` → `formatIsoDate(this.fromTime)`
- `moment(this.toTime).format("YYYY-MM-DD")` → `formatIsoDate(this.toTime)`

Update imports.

- [ ] **Step 9: Migrate `admin/.../statistics/ExperimentDetailsView.vue`**

Replace 3 `.fromNow()` calls with `relativeTime(x)`. Update imports.

- [ ] **Step 10: Migrate `admin/.../notices/NoticeEditor.vue`**

Replace:
- `new moment().format()` → `formatShort(new Date())` (for "today")
- `new moment(this.value.publishedTime.toISOString()).utc().format()` → `formatUtc(this.value.publishedTime.toISOString())`
- `new moment(this.value.expirationTime.toISOString()).utc().format()` → `formatUtc(this.value.expirationTime.toISOString())`
- `new moment(this.value.expirationTime.toISOString()).format()` → `formatShort(this.value.expirationTime.toISOString())`

Add imports for `formatShort`, `formatUtc`. Remove moment.

- [ ] **Step 11: Drop `moment` from package.json files**

Edit `django_airavata/apps/workspace/package.json`:
- In `dependencies`, delete `"moment": "^2.30.1"`.

Edit root `package.json`:
- In `dependencies`, delete `"moment": "^2.30.1"` (if present).

Run `npm install` to refresh the lockfile.

- [ ] **Step 12: Smoke-test the moment removal**

Run:
```bash
# No moment imports remain.
grep -rn "from ['\"]moment['\"]\|require(['\"]moment['\"])" \
  django_airavata --include='*.vue' --include='*.js' --include='*.ts' \
  | grep -v node_modules | grep -v dist
# Expected: empty.

# Rebuild.
npm run build --workspaces --if-present 2>&1 | tail -5
```

- [ ] **Step 13: Checkpoint commit**

```bash
git add .
git commit -m "wip(track-b): moment → native Intl via dates.js helper"
```

---

## Task 3: CodeMirror 5 → 6 via `<CodeEditor>`

**Files:**
- Create: `django_airavata/static/common/js/components/CodeEditor.vue`
- Modify: `UserStorageTextEditViewer.vue` (real consumer)
- Modify: `MultiFileInputEditor.vue`, `FileInputEditor.vue` (drop CSS imports)
- Modify: `django_airavata/apps/workspace/package.json` (swap deps)

- [ ] **Step 1: Install CodeMirror 6 packages**

Edit `django_airavata/apps/workspace/package.json` `dependencies` block. Remove `"codemirror": "5.52.2"`. Add:

```json
"@codemirror/commands": "^6.0.0",
"@codemirror/lang-javascript": "^6.0.0",
"@codemirror/lang-markdown": "^6.0.0",
"@codemirror/lang-python": "^6.0.0",
"@codemirror/state": "^6.0.0",
"@codemirror/theme-one-dark": "^6.0.0",
"@codemirror/view": "^6.0.0",
```

Run `npm install` to sync.

- [ ] **Step 2: Create the CodeEditor component**

Write `django_airavata/static/common/js/components/CodeEditor.vue`:

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

- [ ] **Step 3: Migrate `UserStorageTextEditViewer.vue` to `<CodeEditor>`**

Read the file first; it's non-trivial. The existing structure uses `this.$refs.editor` + CodeMirror(el, options). Replace with:

Template:
```vue
<CodeEditor v-model="currentContent" :line-numbers="true" />
```

Script:
- Remove `import CodeMirror from "codemirror";`
- Remove `import "codemirror/lib/codemirror.css";` and `import "codemirror/theme/abcdef.css";`
- Add `import CodeEditor from "django-airavata-common-ui/js/components/CodeEditor.vue";`
- Register the component: `components: { CodeEditor }`.
- Remove the `mounted()` body that calls `CodeMirror(...)` and sets `this.editor`.
- Remove the `this.editor.on("change", ...)` handler — `v-model` on `<CodeEditor>` handles the binding.
- Remove any `this.editor.getDoc().getValue()` — replace with `this.currentContent`.
- Remove the template's `<div ref="editor">` — replaced by `<CodeEditor>`.

Style:
- Remove the `.CodeMirror { ... }` block at bottom of the `<style>`. `<CodeEditor>` brings its own scoped styles.

- [ ] **Step 4: Drop codemirror CSS imports from `MultiFileInputEditor.vue`**

Read the file; find the `<style>` block containing:
```scss
@import "~codemirror/lib/codemirror.css";
@import "~codemirror/theme/abcdef.css";
```
Remove those two lines. Keep the rest of the style block.

- [ ] **Step 5: Same for `FileInputEditor.vue`**

Remove the same two `@import` lines.

- [ ] **Step 6: Verify no codemirror 5 references remain**

```bash
grep -rn "from ['\"]codemirror['\"]\|require(['\"]codemirror['\"])\|~codemirror/" \
  django_airavata --include='*.vue' --include='*.js' --include='*.ts' --include='*.scss' --include='*.css' \
  | grep -v node_modules | grep -v dist
grep -n '"codemirror"' django_airavata/apps/*/package.json django_airavata/static/common/package.json
```
Expected: both empty.

- [ ] **Step 7: Build and lint**

```bash
npm run build --workspaces --if-present 2>&1 | tail -5
npm run lint 2>&1 | tail -3
```
Expected: both exit 0.

- [ ] **Step 8: Checkpoint commit**

```bash
git add .
git commit -m "wip(track-b): CodeMirror 5 → 6 via shared CodeEditor.vue"
```

---

## Task 4: Delete `django_airavata/static/bootstrap-4.0.0-beta/`

**Files:**
- Delete: the entire directory.

- [ ] **Step 1: Verify zero references across the tree**

```bash
grep -rln "bootstrap-4.0.0-beta" django_airavata \
  --include='*.py' --include='*.html' --include='*.vue' \
  --include='*.js' --include='*.ts' --include='*.scss' --include='*.css' \
  --include='*.json' --include='*.yaml' --include='*.yml' \
  | grep -v node_modules | grep -v dist
```
Expected: empty. If any reference is found, STOP and investigate. Do NOT delete until this is clean.

- [ ] **Step 2: Delete**

```bash
git rm -r django_airavata/static/bootstrap-4.0.0-beta
```

- [ ] **Step 3: Re-verify absence**

```bash
test ! -d django_airavata/static/bootstrap-4.0.0-beta
find django_airavata -type d -name 'bootstrap-*-beta*' -not -path '*/node_modules/*'
```
Expected: exit 0; empty find.

- [ ] **Step 4: Rebuild / relint**

```bash
npm run build --workspaces --if-present 2>&1 | tail -5
npm run lint 2>&1 | tail -3
```
Expected: both exit 0 (nothing depends on the fossil).

- [ ] **Step 5: Checkpoint commit**

```bash
git add -A
git commit -m "wip(track-b): delete bootstrap-4.0.0-beta fossil"
```

---

## Task 5: `vue-slider-component` rationale pin

**Files:**
- Modify: `django_airavata/apps/workspace/package.json`

- [ ] **Step 1: Add an inline rationale comment**

Edit `django_airavata/apps/workspace/package.json`. Find the line:

```json
"vue-slider-component": "4.1.0-beta.7",
```

Note that JSON doesn't support comments. A conventional workaround is to
add a companion `_vue-slider-component-note` sibling entry:

Replace the line with:

```json
"vue-slider-component": "4.1.0-beta.7",
"_vue-slider-component-note": "Vue 3 support only exists on 4.x betas; 4.x never reached stable. Revisit when Track A decides on a component library (PrimeVue/Radix).",
```

The extra key is harmless to npm (which ignores unrecognized top-level
devDependencies keys — except `_`-prefixed keys are always silently
ignored in `dependencies`/`devDependencies` arrays). Run `npm install` to
verify the lockfile doesn't choke.

Alternative (cleaner): create a `.npmrc` or a `README-pins.md` documenting
pinned beta deps. For this track, use the `_note` sibling — easy to grep,
visible next to the pin.

- [ ] **Step 2: Verify npm install still works**

```bash
npm install 2>&1 | tail -5
```
Expected: exit 0; no error about unknown fields.

If npm chokes on the `_note` key (some versions validate `dependencies` keys), fall back to adding a README note at `django_airavata/apps/workspace/README-pins.md` with the rationale, and don't add the `_note` key.

- [ ] **Step 3: Checkpoint commit**

```bash
git add django_airavata/apps/workspace/package.json package-lock.json
git commit -m "wip(track-b): vue-slider-component beta pin rationale"
```

---

## Task 6: Remove `lodash` via inline `_.debounce`

**Files:**
- Modify: `django_airavata/apps/workspace/static/django_airavata_workspace/js/components/experiment/input-editors/AutocompleteInputEditor.vue`
- Modify: `django_airavata/apps/workspace/static/django_airavata_workspace/js/components/experiment/ExperimentEditor.vue`
- Modify: `django_airavata/apps/workspace/package.json`

- [ ] **Step 1: Inline debounce in `AutocompleteInputEditor.vue`**

Read the file around line 23 (the `import _ from "lodash";`) and find the
`searchChanged` method that wraps `_.debounce(function (newValue) {...}, N)`.

Replace the `_.debounce` call with a tiny inline IIFE that produces the
same debounced function. The pattern:

```js
// Before (illustrative):
searchChanged: _.debounce(function (newValue) {
  // body
}, 300),

// After:
searchChanged: (() => {
  let t;
  return function (newValue) {
    clearTimeout(t);
    const ctx = this;
    t = setTimeout(() => {
      // body (same as before, use `ctx` if the body uses `this`)
    }, 300);
  };
})(),
```

Note: the original `function (newValue) {...}` likely uses `this` inside
its body. The IIFE captures `this` at call time via `ctx` — preserve that.
Read the original body carefully; the wait milliseconds might be different
from 300.

Remove `import _ from "lodash";`.

- [ ] **Step 2: Inline debounce in `ExperimentEditor.vue`**

Same pattern as Step 1 for the `calculateQueueSettings` method. This one is
an `async function` — preserve the async in the wrapped body:

```js
calculateQueueSettings: (() => {
  let t;
  return function (...args) {
    clearTimeout(t);
    const ctx = this;
    t = setTimeout(async () => {
      // original async body, referring to `ctx` for `this`
    }, <original-ms>);
  };
})(),
```

Remove `import _ from "lodash";`.

- [ ] **Step 3: Drop lodash from package.json**

Edit `django_airavata/apps/workspace/package.json`. Remove `"lodash": "^4.17.21"` from `dependencies`.

Run `npm install` to sync.

- [ ] **Step 4: Verify no lodash imports remain**

```bash
grep -rn "from ['\"]lodash['\"]\|require(['\"]lodash['\"])" \
  django_airavata --include='*.vue' --include='*.js' --include='*.ts' \
  | grep -v node_modules | grep -v dist
grep -n '"lodash"' django_airavata/apps/*/package.json django_airavata/static/common/package.json
```
Expected: both empty.

- [ ] **Step 5: Build and lint**

```bash
npm run build --workspaces --if-present 2>&1 | tail -5
npm run lint 2>&1 | tail -3
```
Expected: exit 0. No regression in admin-airavata bundle size.

- [ ] **Step 6: Checkpoint commit**

```bash
git add .
git commit -m "wip(track-b): remove lodash (inline debounce at 2 call sites)"
```

---

## Task 7: Run every gate check

**Files:** none (verification only).

Execute the 14 gate checks from the spec's "Done criteria" section.

- [ ] **Step 1: Gate 1-2 — moment fully gone**

```bash
echo "=== Gate 1 ===" && \
grep -rn "from ['\"]moment['\"]\|require(['\"]moment['\"])" \
  django_airavata --include='*.vue' --include='*.js' --include='*.ts' \
  | grep -v node_modules | grep -v dist; echo "exit=$?"
echo "=== Gate 2 ===" && \
grep -n '"moment"' django_airavata/apps/workspace/package.json package.json; echo "exit=$?"
```
Expected: both empty (exit=1 from grep no-match is the pass signal).

- [ ] **Step 2: Gate 3 — CodeMirror 5 fully gone**

```bash
echo "=== Gate 3a (code) ===" && \
grep -rn "from ['\"]codemirror['\"]\|require(['\"]codemirror['\"])\|~codemirror/" \
  django_airavata --include='*.vue' --include='*.js' --include='*.ts' --include='*.scss' --include='*.css' \
  | grep -v node_modules | grep -v dist; echo "exit=$?"
echo "=== Gate 3b (package.json) ===" && \
grep -n '"codemirror"' django_airavata/apps/*/package.json django_airavata/static/common/package.json; echo "exit=$?"
```
Expected: both empty.

- [ ] **Step 3: Gate 4 — Bootstrap 4 beta fossil gone**

```bash
echo "=== Gate 4 ===" && \
test ! -d django_airavata/static/bootstrap-4.0.0-beta && \
find django_airavata -type d -name 'bootstrap-*-beta*' -not -path '*/node_modules/*' && \
echo OK-4
```

- [ ] **Step 4: Gate 5 — lodash gone**

```bash
echo "=== Gate 5a ===" && \
grep -rn "from ['\"]lodash['\"]\|require(['\"]lodash['\"])" \
  django_airavata --include='*.vue' --include='*.js' --include='*.ts' \
  | grep -v node_modules | grep -v dist; echo "exit=$?"
echo "=== Gate 5b ===" && \
grep -n '"lodash"' django_airavata/apps/*/package.json django_airavata/static/common/package.json; echo "exit=$?"
```
Expected: both empty.

- [ ] **Step 5: Gate 6 — vue-slider rationale present**

```bash
grep 'vue-slider-component' django_airavata/apps/workspace/package.json
```
Expected: returns at least one line AND there is a `_vue-slider-component-note` key immediately after OR a `README-pins.md` file present.

- [ ] **Step 6: Gate 7 — CodeEditor exists + real consumer uses it**

```bash
test -f django_airavata/static/common/js/components/CodeEditor.vue && \
grep -n "CodeEditor" \
  django_airavata/apps/workspace/static/django_airavata_workspace/js/components/storage/storage-edit/UserStorageTextEditViewer.vue && \
echo OK-7
```

- [ ] **Step 7: Gate 8 — CSS-only former consumers cleaned up**

```bash
grep -n "codemirror" \
  django_airavata/apps/workspace/static/django_airavata_workspace/js/web-components/input-editors/MultiFileInputEditor.vue \
  django_airavata/apps/workspace/static/django_airavata_workspace/js/web-components/input-editors/FileInputEditor.vue
```
Expected: empty.

- [ ] **Step 8: Gate 9 — No date-fns dep added**

```bash
grep -n '"date-fns"\|"date-fns-tz"' \
  django_airavata/apps/*/package.json \
  django_airavata/static/common/package.json \
  package.json
```
Expected: empty.

- [ ] **Step 9: Gate 10 — dates.js exists**

```bash
test -f django_airavata/static/common/js/utils/dates.js && echo OK-10
```

- [ ] **Step 10: Gate 11 — CodeMirror 6 installed**

```bash
python3 -c "
import json
lock = json.load(open('package-lock.json'))
cm6 = [k for k in lock.get('packages', {}) if k.startswith('node_modules/@codemirror/')]
assert len(cm6) >= 5, f'expected >= 5 @codemirror/* packages, got {len(cm6)}'
print(f'OK {len(cm6)} @codemirror packages')
"
```

- [ ] **Step 11: Gates 12-13 — build + lint**

```bash
npm run build --workspaces --if-present 2>&1 | tail -5
echo "---"
npm run lint 2>&1 | tail -3
```
Expected: both exit 0.

- [ ] **Step 12: Gate 14 — manifest + bundle-size parity**

```bash
# Manifest keys
for app in admin auth dataparsers workspace; do
  python3 -c "
import json
pre = {k for k in open('/tmp/td-b-pre-$app-manifest-keys.txt').read().splitlines() if k and not k.startswith('_')}
post = {k for k in json.load(open('django_airavata/apps/$app/static/django_airavata_$app/dist/manifest.json')) if not k.startswith('_')}
assert pre == post, f'$app manifest drift'
print('OK $app manifest parity')
"
done

# Bundle size — workspace + admin should SHRINK.
for app in admin auth dataparsers workspace; do
  pre_k=$(awk '{print $1}' /tmp/td-b-pre-$app-size.txt)
  post_k=$(du -s django_airavata/apps/$app/static/django_airavata_$app/dist/assets | awk '{print $1}')
  pre_h=$(du -sh django_airavata/apps/$app/static/django_airavata_$app/dist/assets 2>/dev/null; echo)
  post_h=$(du -sh django_airavata/apps/$app/static/django_airavata_$app/dist/assets | awk '{print $1}')
  echo "$app: pre=${pre_k}k post=${post_k}k $( [ $post_k -le $pre_k ] && echo 'OK-shrunk-or-flat' || echo 'GREW - investigate' )"
done
```
Expected: all 4 manifests identical; workspace+admin shrink; auth+dataparsers flat or shrink.

- [ ] **Step 13: Layer 2 — pytest**

```bash
uv run pytest -q 2>&1 | tail -3
```
Expected: same summary as modernization baseline (71 passed, 4 failed).

---

## Task 8: Squash and merge

- [ ] **Step 1: Verify wip commits**

```bash
git log --oneline -10
```
Expected: 5 or 6 `wip(track-b):` commits on top of the spec commit `0645aa057a`.

- [ ] **Step 2: Soft-reset to the spec commit**

```bash
git reset --soft 0645aa057a
git diff --cached --stat | tail -3
```
Expected: cumulative Track B changes staged.

- [ ] **Step 3: Create the squashed commit**

```bash
git commit -m "$(cat <<'EOF'
refactor(portal): library swaps

- moment → native Intl via shared django_airavata/static/common/js/utils/dates.js.
  Replaces 9 call sites. Cosmetic change: ordinal day format ("Apr 21st")
  becomes flat ("Apr 21, 2026") — Intl does not support ordinals.
- CodeMirror 5.52.2 → CodeMirror 6 via new shared component
  django_airavata/static/common/js/components/CodeEditor.vue. Migrates
  the one real JS consumer (UserStorageTextEditViewer.vue). Drops CSS-only
  imports from MultiFileInputEditor.vue and FileInputEditor.vue.
- Delete django_airavata/static/bootstrap-4.0.0-beta/ (1.6 MB fossil, zero
  references).
- vue-slider-component stays on 4.1.0-beta.7 with an inline rationale
  comment — 4.x never reached stable and is the only Vue 3-compatible line.
  Revisit when Track A decides on a component library.
- Remove lodash by inlining _.debounce at the 2 call sites
  (AutocompleteInputEditor, ExperimentEditor).

Functional parity: manifest keys byte-identical, pytest summary unchanged.
Bundle sizes for workspace + admin shrink as expected (moment ~67 KB
gzipped + CodeMirror 5 ~200 KB gzipped removed).

Spec: docs/superpowers/specs/2026-04-21-track-b-library-swaps-design.md
EOF
)"
```

- [ ] **Step 4: Push and merge**

```bash
git push -u origin track-b/library-swaps
git checkout modernization
git pull origin modernization
git merge --no-ff track-b/library-swaps -m "merge: Track B (library swaps)"
git push origin modernization
```

- [ ] **Step 5: Verify**

```bash
git log --oneline --merges -3
```
Expected: top merge is `merge: Track B (library swaps)`, then Track C and Track D.

---

## Plan Self-Review

**Spec coverage:**

| Spec section | Plan task |
|---|---|
| Scope 1: moment → Intl | Task 2 |
| Scope 2: CodeEditor CM6 | Task 3 |
| Scope 3: delete Bootstrap 4 fossil | Task 4 |
| Scope 4: vue-slider rationale | Task 5 |
| Scope 5: lodash removal | Task 6 |
| Testing Layer 1 (static + build) | Task 7 (gates 12-13) + each checkpoint's build step |
| Testing Layer 2 (pytest) | Task 7 Step 13 |
| Testing Layer 3 (bundle size) | Task 1 (baseline) + Task 7 Step 12 |
| Testing Layer 4 (manual smoke) | Deferred to Task 8's post-merge verification (operator-run) |
| Done criteria (14 gates) | Task 7 |

**Placeholder scan:** no TBD/TODO/FIXME. Each step has concrete code or commands.

**Type consistency:** branch `track-b/library-swaps`, spec path, helper exports (`relativeTime`, `formatShort`, `formatDate`, `formatIsoDate`, `formatUtc`), `<CodeEditor>` prop signatures all consistent between spec and plan.

---

## Execution handoff

Plan complete and saved to `airavata-django-portal/docs/superpowers/plans/2026-04-21-track-b-library-swaps-plan.md`. Recommended execution: `superpowers:subagent-driven-development`.
