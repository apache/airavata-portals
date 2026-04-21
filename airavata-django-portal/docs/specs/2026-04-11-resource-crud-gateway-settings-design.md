# Storage/Compute CRUD + Gateway Settings

**Date:** 2026-04-11
**Status:** Draft
**Scope:** Sub-project 2 of 4 (Portal Functionality)
**Depends on:** Sub-project 1 (SSE + Interactive SSH Proxy)

## Overview

Make Storage and Compute resource pages fully functional with detail pages for viewing, editing, credential assignment, connection testing, and HPC discovery. Make Gateway Settings load and save real data.

## Storage Resource Detail Page

**Route:** `/resources/storage/<storage_resource_id>`

### Layout

**Header row:** Resource name (h4) + Enabled badge + "Test Connection" button (btn-primary btn-sm) + "Delete" button (btn-outline-danger btn-sm)

**Card 1 — General:**

- Host Name — text input, required
- Description — textarea, optional
- Enabled — checkbox toggle

**Card 2 — Credentials:**

- SSH Credential — dropdown selector (reuses `SSHCredentialSelector` from admin app via cross-app import)
- "Create New" inline button to generate a new SSH key
- "Test Connection" button — calls `POST /api/ssh/test/` with `{hostname, port: 22, credential_token}`
- Connection status indicator: idle (gray), testing (spinner), connected (green check), failed (red X with message)
- Interactive auth prompts handled automatically by `SshPromptNotification` via SSE

**Card 3 — Data Movement (read-only placeholder):**

- Table showing current data movement interfaces (protocol, priority)
- Future: upload/download test buttons

**Save button** at bottom right — calls `StorageResourceService.update({lookup: id, data: {...}})`

**Back link** at top — "Back to storage list" → `/resources/storage`

### Navigation

- From storage list table, clicking resource name navigates to `/resources/storage/<id>`
- After save, stays on detail page with success notification
- After delete, navigates back to list

## Compute Resource Detail Page

**Route:** `/resources/compute/<compute_resource_id>`

### Layout

**Header row:** Resource name (h4) + Enabled badge + "Test Connection" + "Delete"

**Card 1 — General:**

- Host Name — text input, required
- Description — textarea, optional
- Enabled — checkbox toggle
- CPUs Per Node — number input
- Max Memory Per Node — number input
- Default Node Count — number input
- Default CPU Count — number input
- Default Walltime (minutes) — number input

**Card 2 — Credentials:**

- SSH Credential selector (same as storage)
- "Test Connection" button
- Connection status indicator
- After successful connection: "Discover HPC Info" button appears (btn-outline-primary btn-sm)

**Card 3 — HPC Configuration:**

- Populated automatically by "Discover HPC Info" (runs `info.sh` via `/api/ssh/run-info/`)
- Or manually editable
- Table of batch queues/partitions:
    - Partition name
    - Max nodes
    - Max CPUs per node
    - Max memory (MB) per node
    - Max GPUs per node
    - GPU types (comma-separated)
    - Accounts (comma-separated)
- "Add Partition" button for manual entry
- Delete action per row
- Maps to Airavata's `batchQueues` field

**Card 4 — Job Submission:**

- Resource Manager Type: dropdown (SLURM, PBS, SGE, FORK)
- SSH Port — number input (default 22)
- Alternative SSH Hostname — text input (optional)
- Maps to Airavata's `jobSubmissionInterfaces`

**Save button** — calls `ComputeResourceService.update({lookup: id, data: {...}})`

### HPC Discovery Flow

1. User clicks "Test Connection" with a credential selected
2. SSH connects (interactive prompts via SSE if needed)
3. On success, "Discover HPC Info" button appears
4. User clicks it → calls `POST /api/ssh/run-info/` with `{session_id}`
5. Server runs `info.sh` on the remote host
6. Response contains parsed partitions array
7. Frontend auto-populates the batch queues table
8. User reviews, edits if needed, then saves

## Gateway Settings (Functional)

**Route:** `/gateway/settings` (existing page)

### Load

On mount, calls:

- `GET /api/gateway-resource-profile/` — fetches gateway resource profile (existing admin API endpoint, already works)
- `StorageResourceService.names()` — populates storage dropdown
- `CredentialSummaryService.allSSHCredentials()` — populates credential dropdown

### Fields

- **Gateway ID** — read-only, from `settings.GATEWAY_ID`
- **Gateway Name** — read-only, from `settings.PORTAL_TITLE` (displayed, not editable via API)
- **Default Storage Resource** — dropdown, maps to gateway profile's storage preferences
- **Default SSH Credential** — dropdown (SSHCredentialSelector), maps to gateway profile's credential token
- **File System Root** — text input, maps to storage preference's `fileSystemRootLocation`
- **Appearance** section — read-only with note "Configure in settings_local.py"
- **Notifications** section — read-only with note "Configure in settings_local.py"

### Save

Calls existing admin API:

- `PUT /api/gateway-resource-profile/` with updated storage preference and credential token

## Backend Changes

### ViewSet Updates (`apps/api/views.py`)

**StorageResourceViewSet:**

- Add `mixins.UpdateModelMixin` to base classes
- Add `perform_update(serializer)` — converts proto_compat to protobuf `StorageResourceDescriptionProto`, calls `storage.update_storage_resource(id, proto)`
- Add proto-to-compat conversion in `get_instance()` (same pattern as `ProjectViewSet._proto_to_compat`)

**ComputeResourceViewSet:**

- Add `perform_update(serializer)` (already inherits from `APIBackedViewSet` which has `UpdateModelMixin`)
- Add proto-to-compat conversion in `get_instance()`

### Service Config (`service_config.js`)

```javascript
StorageResources: { viewSet: ["retrieve", "create", "update", "delete"], ... }
ComputeResources: { viewSet: ["retrieve", "create", "update", "delete"], ... }
```

### New Files

| File                                    | Purpose                             |
| --------------------------------------- | ----------------------------------- |
| `entry-storage-detail.js`               | Entry point for storage detail page |
| `entry-compute-detail.js`               | Entry point for compute detail page |
| `containers/StorageDetailContainer.vue` | Storage resource detail/edit page   |
| `containers/ComputeDetailContainer.vue` | Compute resource detail/edit page   |

### New URL Routes (`urls.py`)

Root urls.py additions:

```python
re_path(r"^resources/storage/(?P<storage_resource_id>[^/]+)$", workspace_views.storage_detail, name="storage_detail"),
re_path(r"^resources/compute/(?P<compute_resource_id>[^/]+)$", workspace_views.compute_detail, name="compute_detail"),
```

### Vite Config

Add entries: `"storage-detail"`, `"compute-detail"`

### ENTRY_POINTS Dict

Add: `"storage-detail"`, `"compute-detail"` pointing to new entry JS files

## Cross-App Component Import

`SSHCredentialSelector.vue` from admin app is imported into workspace detail pages using the same cross-app import pattern as `CredentialStoreDashboard.vue`:

```javascript
import SSHCredentialSelector from "../../../../admin/static/django_airavata_admin/src/components/credentials/SSHCredentialSelector.vue";
```

## Testing Plan

1. Navigate to `/resources/storage` → click resource name → detail page loads with current values
2. Change description → Save → reload → change persists
3. Select credential → Test Connection → success notification (key auth to SFTP container)
4. Navigate to `/resources/compute` → click resource name → detail page loads
5. Select credential → Test Connection → interactive prompt if needed
6. Click "Discover HPC Info" → partitions table populated from info.sh output
7. Save → batch queues persisted to Airavata
8. `/gateway/settings` → loads current gateway profile → change storage preference → save → reload → persists
