# Generic Experiment Launcher Design Spec

**Date:** 2026-04-24
**Branch:** `feat/generic-experiment-launcher` (off `modernization`)
**Scope:** Replace the per-application experiment launch flow in `airavata-django-portal` with a single generic launcher page.

---

## Goal

One URL that handles the whole launch flow: pick application → pick interface → give inputs (scalar + file I/O with storage pickers) → choose runtime → preview the job submission script → launch. Three-tab single-page wizard with strict forward gating.

## Assumed Upstream (tracked separately)

This spec assumes two backend changes have landed in the Airavata Java server before the portal work merges:

1. **New application model** — apps consist of (a) content reference (tarball or GitHub URL) and (b) user-defined interfaces with typed input/output signatures. No per-app queue defaults, walltime suggestions, or compute-resource deployment pins.
2. **Dry-run RPC** — `GenerateExperimentSubmissionScript(draft) → { invocation_command, script_contents, warnings[] }`. Runs the compute-service → agent-service → research-framework chain in dry-run mode; same code path as launch but stops before the scheduler call.

Script generation is layered: compute-service renders the Groovy-based base with scheduler directives (e.g., `#SBATCH`) and module loads; agent-service appends the agent sidecar startup; research-framework appends stage-in, command invocation, and stage-out. On SLURM resources the script runs via `sbatch script.sh`; elsewhere via `bash script.sh`, and `#SBATCH` directives are omitted.

The portal cannot ship without both upstream pieces. Jira/airavata ticket references belong in the PR header when opened.

## Scope & URL Structure

- **New URL:** `/workspace/launch` — single Django view rendering a Vue mount point.
- **Removed:** `/workspace/applications/<app_module_id>/create_experiment` (old per-app launch) and `/workspace/applications` (app tile grid). App discovery now lives inside Tab 1.
- **Redirects:** both old URLs 301 to `/workspace/launch`. `app_module_id` is not preserved — it referenced the pre-restructure application model and is no longer usable.
- **Repo-internal call sites updated in this PR:** `WorkspaceDashboardContainer`, `DashboardContainer`, `ProjectOverviewContainer`, `ExperimentListContainer`, `ApplicationEditorContainer`, dataparsers output views, and the SDK's `experiment_util` helper (with a deprecation shim for downstream gateway consumers).

## Frontend Architecture

- **Entry point:** `django_airavata/apps/workspace/static/django_airavata_workspace/js/entry-launch.ts`. Vue 3 `<script setup lang="ts">` throughout (matches Track A).
- **Component tree:**
  ```
  LaunchContainer
    ExperimentMetaHeader          (name + project + description)
    WizardTabs                    (3 tabs, strict-forward gating)
    Tab1ApplicationInputs
      AppPicker                   (category chips + search + tile grid)
      InterfacePicker             (verb cards for the selected app)
      InputList                   (scalar + file, mixed; file rows have storage + path + stage-in badge)
      OutputList                  (file outputs: target storage + path + stage-out badge)
    Tab2Runtime                   (compute / partition / walltime / nodes / CPUs / allocation readout)
    Tab3ReviewLaunch              (invocation command + read-only script + launch button)
  ```
- **State:** Pinia store `stores/launch.ts` (`useLaunchStore`) owns the entire draft — metadata, picked app, picked interface, inputs map, outputs map, runtime selections, preview result, per-tab validation (derived getter). Tabs are dumb views.
- **In-page nav:** URL query param `?tab=1|2|3`. Browser back/forward works inside the wizard. Strict forward gate implemented in `WizardTabs` by checking per-tab validity from the store.
- **Draft persistence:** localStorage keyed by `user_id + draft_uuid`. Restored on mount, cleared on successful launch. Server-side drafts are out of scope for v1.
- **Reuse:** the core input widgets from `ComputationalResourceSchedulingEditor` and `QueueSettingsEditor` get extracted into leaner `<script setup>` components under `components/launch/runtime/`. The original editor components (used only by the dying ExperimentEditor) go away with it.
- **Deleted:** `CreateExperimentContainer.vue`, `EditExperimentContainer.vue`, `ExperimentEditor.vue`, `ComputationalResourceSchedulingEditor.vue`, `QueueSettingsEditor.vue`, `GroupResourceProfileSelector.vue`, `ApplicationListContainer` (if present), `entry-create-experiment.js`, `entry-edit-experiment.js`. The existing-experiment detail page stays; editing of in-flight experiments is dropped (the old draft shape is not meaningful under the new app model).

## Backend API Surface

**New Django REST endpoints** (in `django_airavata/apps/api/`):

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/applications/?category=&search=` | list apps with content ref + declared interfaces + category |
| GET | `/api/applications/<app_id>/` | single app detail (same shape) |
| GET | `/api/projects/<project_id>/resource-profile/` | resolved profile: allowed compute resources, partitions per resource, allocation id |
| GET | `/api/user-storages/` | storages the current user can access |
| POST | `/api/experiments/preview/` | body: experiment draft. Returns `{ invocation_command, script_contents, warnings[] }`. Thin proxy to the airavata dry-run RPC. |
| POST | `/api/experiments/` | existing endpoint, updated to accept the new draft shape. Launches (no separate submit call). |

**Experiment draft schema** (REST JSON + matching Thrift):

```json
{
  "name": "string (≤256)",
  "project_id": "string",
  "description": "string (optional)",
  "app_id": "string",
  "interface_name": "string",
  "inputs":  { "<name>": "<scalar> | { \"storage_id\": \"…\", \"path\": \"…\" }" },
  "outputs": { "<name>": { "storage_id": "…", "path": "…" } },
  "runtime": {
    "compute_resource_id": "string",
    "partition": "string",
    "walltime": "HH:MM:SS",
    "nodes": 1,
    "cpus_per_node": 1
  }
}
```

Interim storage is not in the schema. The server derives it from `compute_resource_id` + `project_id` (every compute resource has a 1-1 mapped storage resource; the project gets a scratch subdir under that storage).

Resource profile resolution: each project has a resource profile attached (configured by the project admin). Switching projects at launch time switches the allowed compute resources, partitions, and allocation id. There is no user-level aggregation.

**Error shapes:**

- `400 { field: [msgs] }` — server-side validation failures. The portal renders them inline on the offending row or field.
- `502 { message }` — airavata unreachable. Preview shows error banner; launch button disabled.
- `409 { message, field }` — referenced storage path inaccessible to user. Surfaces on the offending input row.

## Tab-by-Tab Specification

### Top strip (persistent across tabs)
- Experiment name — required, ≤ 256 characters.
- Project — required dropdown from user's project list.
- Description — optional multiline.
- Changing Project invalidates Tab 2's compute resource, partition, and allocation readout. If user is on Tab 2 when this happens, a warning toast fires.

### Tab 1 — Application & Inputs
Progressive disclosure, all in one tab:

1. **Application** — category chip row with counts (chips from `/api/applications/` grouped); "All" default. Search box narrows within the active chip. Tile grid is server-paginated (50 per page). Selecting an app collapses the grid to a compact summary with a "change" link.
2. **Interface** — card row showing the selected app's user-defined verbs with I/O signatures (e.g., `run(sim_dir, force_field, steps:int) → trajectory`). Required pick; first interface auto-selected.
3. **Inputs** — one row per declared input:
   - Scalar (`int`, `float`, `string`, `bool`, `enum`, `multi-string`): existing `input-editors/*.vue` widgets reused, typed via the signature.
   - File/dir: `[name+type-tag] [storage select] [path input with browse-tree modal] [stage-in badge]`. Storage select default = user's primary storage.
4. **Outputs** — one row per file/dir output: `[name+type-tag] [target storage select] [path input] [stage-out badge]`. Scalar outputs get no row (returned in the job result).

**Tab 1 validity:** name + project set, app picked, interface picked, every required input has a value, every file I/O row has storage + path.

Changing app clears interface + inputs + outputs (warned). Changing interface clears inputs + outputs (warned).

### Tab 2 — Runtime
- Compute resource — dropdown from the selected project's resolved resource profile.
- Partition — dropdown from the compute resource's profile entry.
- Walltime — `HH:MM:SS` input, validated against partition max walltime.
- Nodes — integer, validated against partition max nodes.
- CPUs per node — integer, validated against partition spec.
- Allocation ID — read-only badge, auto-filled from project's profile. For SLURM resources this is the value for `-A`.
- Compute storage — read-only badge showing the compute resource's 1-1 mapped storage resource and the project scratch path (where interim storage lives for this run).

**Tab 2 validity:** all five inputs set and within partition limits.

### Tab 3 — Review & Launch
- On entry: hash the draft; if hash matches the last-rendered one, serve cached preview. Otherwise fire `POST /api/experiments/preview/` with loading skeleton (~1-3s expected).
- Success: invocation command banner (`sbatch <path>` or `bash <path>`) + syntax-highlighted read-only script. `warnings[]` shown above the script as a yellow banner list (non-blocking). Launch button enabled.
- Failure: error banner with retry button. Launch button disabled.
- Launch: `POST /api/experiments/` with same draft. On success, redirect to `/workspace/experiments/<id>`. On failure, red banner with the server error + try-again button; stays on Tab 3. Draft is not cleared from localStorage until launch actually succeeds.

## Error & Edge-Case Handling

- **Preview freshness:** draft-hash cache prevents re-rendering when user bounces Tab 3 ↔ Tab 1 without editing.
- **Preview in-flight + nav-away:** pending request cancelled via `AbortController` when user leaves Tab 3.
- **Launch failure:** stays on Tab 3 with retry; draft preserved in localStorage.
- **Session expiry:** 401 on any API call → redirect to `/auth/login?next=/workspace/launch`. On return, `LaunchContainer` hydrates from localStorage.
- **Network offline:** API layer retries once with backoff; if still offline, tab-level error with "Can't reach the portal — check your connection"; launch disabled.
- **Partial dependency load:** storages fail / apps succeed → storage dropdowns show "Can't load storages — retry"; rest of Tab 1 usable. Apps fail → whole tab shows error; no progress.
- **Draft reuse across devices:** localStorage is per-device. V1 accepts this.
- **Project / app / interface change mid-flow:** downstream tab state cleared with a warning toast naming what's being reset.

## Testing Strategy

- **Unit (Vitest):** one spec per component with logic — `AppPicker` (filter + search), `InterfacePicker` (selection + signature propagation), `InputList` (scalar vs file row routing), `Tab2Runtime` (profile-driven dropdowns, partition validation), `LaunchContainer` (tab-gating derivation). Separate spec for `useLaunchStore` (draft hash, tab-validity getters, interim-storage derivation, project-change reset).
- **Integration (Vitest + `@vue/test-utils` + `happy-dom`):** full-flow spec with API layer mocked — happy path, project-change invalidation, interface-change clearing, preview failure → retry. No network.
- **E2E (Playwright):** extends `tests/e2e/specs/`:
  - `launch-happy.spec.ts` — login, navigate, pick app + interface, fill inputs, set runtime, preview, launch, assert redirect to experiment detail.
  - `launch-error-paths.spec.ts` — preview failure (mock 502), strict-forward gate (click blocked tab), project change invalidates tab 2.
  - `smoke.spec.ts` gets `/workspace/launch` added to `AUTHENTICATED_PAGES`.
- **Backend (Django):** one `TestCase` per new DRF view — happy path + auth + 4xx shapes. `preview` view tested with the Thrift client mocked (live Java dry-run is out of scope for portal CI).
- **Contract tests:** JSON schemas under `tests/contracts/` for the experiment-draft payload and preview response. Both Vitest and Django tests import them so contract drift is caught.
- **Manual checklist in PR template:** each I/O type exercised once, project swap mid-flow, app swap mid-flow, session expiry on Tab 3, live dry-run against a running dev stack.

## Migration & Rollout

1. Airavata server merges new app model + dry-run RPC (tracked separately).
2. Portal branch consumes the new APIs, gated behind a `FEATURE_GENERIC_LAUNCHER` flag in `settings.py` (default off).
3. Verified end-to-end against a live dev stack.
4. Flag removed in a single commit that flips it globally on.
5. Playwright smoke expanded to cover `/workspace/launch`; failing smoke blocks merge.

**Deleted code (same PR):** see Frontend Architecture → Deleted.

**Added code (same PR):** `entry-launch.ts`, `containers/LaunchContainer.vue`, `components/launch/**`, `stores/launch.ts`, new DRF views + serializers in `apps/api/views.py` and `apps/api/serializers.py`, new URL entries in `apps/api/urls.py`, new `launch(request)` view and `/workspace/launch` route in `apps/workspace/views.py` and `urls.py`, 301 redirects for the old routes.

## Out of Scope (explicit)

- App definition UI for the new model (admins register apps with content + interfaces). Separate track.
- Experiment edit flow under the new model.
- Server-side drafts.
- Per-output multi-file globs (outputs are single file/dir pointers).

## Open Questions / Coordination

- Exact naming and Thrift signature of the dry-run RPC needs to match what the airavata team commits to. Portal implementation blocks on that contract.
- Resource profile attached to project: the existing project model already carries a GroupResourceProfile reference; the new "resource profile" is expected to supersede or extend that. Portal should confirm the field name on `Project` that resolves to this new profile before implementing the `GET /api/projects/<id>/resource-profile/` view.
