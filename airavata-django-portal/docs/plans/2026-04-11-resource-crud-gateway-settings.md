# Storage/Compute CRUD + Gateway Settings — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add detail/edit pages for Storage and Compute resources with credential pickers, SSH connection testing, HPC discovery, and functional Gateway Settings that load/save via the API.

**Architecture:** New detail page Vue components for storage and compute resources mounted at `/resources/storage/<id>` and `/resources/compute/<id>`. Each imports the existing `SSHCredentialSelector` for credential assignment and calls the SSE+SSH proxy API for connection testing. Gateway Settings rewired to load/save via the existing gateway resource profile REST API.

**Tech Stack:** Django 5.1, Vue 3, Bootstrap 5, asyncssh (via sub-project 1 SSE infrastructure)

---

### Task 1: Backend — Add Update Support to ViewSets

**Files:**
- Modify: `django_airavata/apps/api/views.py` (StorageResourceViewSet ~line 1411, ComputeResourceViewSet ~line 626)
- Modify: `django_airavata/apps/api/static/django_airavata_api/js/service_config.js` (lines 118, 423)

- [ ] **Step 1: Add UpdateModelMixin and perform_update to StorageResourceViewSet**

In `django_airavata/apps/api/views.py`, find `class StorageResourceViewSet` (line 1411). Change the class declaration and add `perform_update`:

Change:
```python
class StorageResourceViewSet(mixins.CreateModelMixin, mixins.RetrieveModelMixin, mixins.DestroyModelMixin, GenericAPIBackedViewSet):
```
To:
```python
class StorageResourceViewSet(mixins.CreateModelMixin, mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin, GenericAPIBackedViewSet):
```

Add after `perform_create`:
```python
    def perform_update(self, serializer):
        from airavata_sdk.generated.org.apache.airavata.model.appcatalog.storageresource.storage_resource_pb2 import (
            StorageResourceDescription as StorageResourceDescriptionProto,
        )

        compat_obj = serializer.save()
        resource_id = getattr(compat_obj, "storageResourceId", "")
        proto_obj = StorageResourceDescriptionProto(
            storage_resource_id=resource_id,
            host_name=getattr(compat_obj, "hostName", ""),
            storage_resource_description=getattr(compat_obj, "storageResourceDescription", ""),
            enabled=getattr(compat_obj, "enabled", True),
        )
        self.request.airavata_client.storage.update_storage_resource(resource_id, proto_obj)
```

Also add proto-to-compat conversion to `get_instance`:
```python
    def get_instance(self, lookup_value: str, format: str | None = None) -> Any:
        from django_airavata.proto_compat import StorageResourceDescription as StorageCompat

        proto = self.request.airavata_client.storage.get_storage_resource(lookup_value)
        return StorageCompat(
            storageResourceId=proto.storage_resource_id,
            hostName=proto.host_name,
            storageResourceDescription=proto.storage_resource_description,
            enabled=proto.enabled,
            creationTime=proto.creation_time if proto.creation_time else None,
            updateTime=proto.update_time if proto.update_time else None,
        )
```

- [ ] **Step 2: Add perform_update and proto conversion to ComputeResourceViewSet**

In `ComputeResourceViewSet` (line 626), add after `perform_create`:
```python
    def perform_update(self, serializer: Any) -> None:
        from airavata_sdk.generated.org.apache.airavata.model.appcatalog.computeresource.compute_resource_pb2 import (
            ComputeResourceDescription as ComputeResourceDescriptionProto,
        )

        compat_obj = serializer.save()
        resource_id = getattr(compat_obj, "computeResourceId", "")
        proto_obj = ComputeResourceDescriptionProto(
            compute_resource_id=resource_id,
            host_name=getattr(compat_obj, "hostName", ""),
            resource_description=getattr(compat_obj, "resourceDescription", ""),
            enabled=getattr(compat_obj, "enabled", True),
            max_memory_per_node=getattr(compat_obj, "maxMemoryPerNode", 0),
            cpus_per_node=getattr(compat_obj, "cpusPerNode", 0),
            default_node_count=getattr(compat_obj, "defaultNodeCount", 0),
            default_cpu_count=getattr(compat_obj, "defaultCPUCount", 0),
            default_walltime=getattr(compat_obj, "defaultWalltime", 0),
        )
        self.request.airavata_client.compute.update_compute_resource(resource_id, proto_obj)
```

Update `get_instance` to convert proto to compat:
```python
    def get_instance(self, lookup_value: str, format: str | None = None) -> Any:
        from django_airavata.proto_compat import ComputeResourceDescription as ComputeCompat

        proto = self.request.airavata_client.compute.get_compute_resource(lookup_value)
        return ComputeCompat(
            computeResourceId=proto.compute_resource_id,
            hostName=proto.host_name,
            resourceDescription=proto.resource_description,
            enabled=proto.enabled,
            maxMemoryPerNode=proto.max_memory_per_node,
            cpusPerNode=proto.cpus_per_node,
            defaultNodeCount=proto.default_node_count,
            defaultCPUCount=proto.default_cpu_count,
            defaultWalltime=proto.default_walltime,
            batchQueues=[],
        )
```

Also update the `get_list` method to use the same conversion:
```python
    def get_list(self) -> list[Any]:
        from django_airavata.proto_compat import ComputeResourceDescription as ComputeCompat

        all_names = self.request.airavata_client.compute.get_all_compute_resource_names()
        results = []
        for rid in all_names:
            proto = self.request.airavata_client.compute.get_compute_resource(rid)
            results.append(ComputeCompat(
                computeResourceId=proto.compute_resource_id,
                hostName=proto.host_name,
                resourceDescription=proto.resource_description,
                enabled=proto.enabled,
                maxMemoryPerNode=proto.max_memory_per_node,
                cpusPerNode=proto.cpus_per_node,
                defaultNodeCount=proto.default_node_count,
                defaultCPUCount=proto.default_cpu_count,
                defaultWalltime=proto.default_walltime,
                batchQueues=[],
            ))
        return results
```

- [ ] **Step 3: Add "update" to JS service config**

In `django_airavata/apps/api/static/django_airavata_api/js/service_config.js`:

Line 118 — change `viewSet: ["retrieve", "create", "delete"]` to:
```javascript
    viewSet: ["retrieve", "create", "update", "delete"],
```

Line 423 — change `viewSet: ["retrieve", "create", "delete"]` to:
```javascript
    viewSet: ["retrieve", "create", "update", "delete"],
```

- [ ] **Step 4: Rebuild API library**

```bash
cd /Users/yasith/code/artisan/airavata-portals/main/airavata-django-portal/django_airavata/apps/api
npx vite build
```

---

### Task 2: Routes and Views for Detail Pages

**Files:**
- Modify: `django_airavata/urls.py` (add detail routes)
- Modify: `django_airavata/apps/workspace/views.py` (add detail view functions)
- Modify: `django_airavata/apps/workspace/vite.config.js` (add entry points)

- [ ] **Step 1: Add detail routes to root urls.py**

In `django_airavata/urls.py`, the current line 24 is:
```python
    re_path(r"^resources/storage", workspace_views.user_storage, name="storage"),
```

Replace lines 24-25 with (detail routes BEFORE list routes so they match first):
```python
    re_path(r"^resources/storage/(?P<storage_resource_id>[^/]+)$", workspace_views.storage_detail, name="storage_detail"),
    re_path(r"^resources/storage$", workspace_views.user_storage, name="storage"),
    re_path(r"^resources/compute/(?P<compute_resource_id>[^/]+)$", workspace_views.compute_detail, name="compute_detail"),
    re_path(r"^resources/compute$", workspace_views.compute_resources, name="compute"),
```

- [ ] **Step 2: Add detail view functions to workspace views.py**

In `django_airavata/apps/workspace/views.py`, add to ENTRY_POINTS dict:
```python
    "storage-detail": "static/django_airavata_workspace/js/entry-storage-detail.js",
    "compute-detail": "static/django_airavata_workspace/js/entry-compute-detail.js",
```

Add view functions (after `compute_resources`):
```python
@login_required
def storage_detail(request, storage_resource_id):
    request.active_nav_item = "storage"
    return render(
        request,
        "django_airavata_workspace/base.html",
        {
            "bundle_name": "storage-detail",
            "entry_point": ENTRY_POINTS["storage-detail"],
            "storage_resource_id": storage_resource_id,
        },
    )


@login_required
def compute_detail(request, compute_resource_id):
    request.active_nav_item = "compute"
    return render(
        request,
        "django_airavata_workspace/base.html",
        {
            "bundle_name": "compute-detail",
            "entry_point": ENTRY_POINTS["compute-detail"],
            "compute_resource_id": compute_resource_id,
        },
    )
```

- [ ] **Step 3: Add Vite entry points**

In `django_airavata/apps/workspace/vite.config.js`, add to the `input` object (after the `"gateway-settings"` entry):
```javascript
        "storage-detail": resolve(
          __dirname,
          "./static/django_airavata_workspace/js/entry-storage-detail.js"
        ),
        "compute-detail": resolve(
          __dirname,
          "./static/django_airavata_workspace/js/entry-compute-detail.js"
        ),
```

- [ ] **Step 4: Update the workspace base template to pass resource IDs**

The workspace `base.html` template already passes `bundle_name` as a div ID. The detail views pass `storage_resource_id` / `compute_resource_id` as context. We need the template to emit these as `data-*` attributes.

Read `django_airavata/apps/workspace/templates/django_airavata_workspace/base.html`. The div is:
```html
<div id="{{ bundle_name }}"></div>
```

Change to:
```html
<div id="{{ bundle_name }}" {% if storage_resource_id %}data-storage-resource-id="{{ storage_resource_id }}"{% endif %} {% if compute_resource_id %}data-compute-resource-id="{{ compute_resource_id }}"{% endif %}></div>
```

---

### Task 3: Storage Detail Page (Vue Component)

**Files:**
- Create: `django_airavata/apps/workspace/static/django_airavata_workspace/js/entry-storage-detail.js`
- Create: `django_airavata/apps/workspace/static/django_airavata_workspace/js/containers/StorageDetailContainer.vue`

- [ ] **Step 1: Create entry point**

Create `entry-storage-detail.js`:
```javascript
import { h } from "vue";
import { components, entry } from "django-airavata-common-ui";
import StorageDetailContainer from "./containers/StorageDetailContainer.vue";

entry(({ createApp }) => {
  const el = document.getElementById("storage-detail");
  const storageResourceId = el ? el.dataset.storageResourceId : null;
  const app = createApp({
    render() {
      return h(components.MainLayout, null, {
        default: () => h(StorageDetailContainer, { storageResourceId }),
      });
    },
  });
  app.mount("#storage-detail");
});
```

- [ ] **Step 2: Create StorageDetailContainer.vue**

Create `containers/StorageDetailContainer.vue`:
```vue
<template>
  <div>
    <div class="mb-2">
      <a href="/resources/storage" class="text-muted" style="font-size:0.8125rem;">
        <i class="fa fa-arrow-left me-1"></i>Back to storage list
      </a>
    </div>

    <div v-if="loading" class="text-center py-4 text-muted">
      <i class="fa fa-spinner fa-spin me-1"></i> Loading...
    </div>

    <template v-if="resource">
      <!-- Header -->
      <div class="d-flex align-items-center justify-content-between mb-3">
        <div>
          <h1 class="h4 mb-0">{{ resource.hostName }}</h1>
          <span class="badge" :class="resource.enabled ? 'bg-success' : 'bg-secondary'">
            {{ resource.enabled ? 'Enabled' : 'Disabled' }}
          </span>
        </div>
        <div class="d-flex gap-2">
          <button class="btn btn-primary btn-sm" @click="testConnection" :disabled="!selectedCredential || connectionStatus === 'testing'">
            <i class="fa fa-plug me-1"></i>Test Connection
          </button>
          <button class="btn btn-outline-danger btn-sm" @click="confirmDelete">
            <i class="fa fa-trash me-1"></i>Delete
          </button>
        </div>
      </div>

      <!-- General -->
      <div class="card mb-3">
        <div class="card-body">
          <h2 class="h6 mb-3">General</h2>
          <div class="row g-3">
            <div class="col-md-6">
              <label class="form-label">Host Name <span class="text-danger">*</span></label>
              <input class="form-control form-control-sm" v-model="resource.hostName" />
            </div>
            <div class="col-md-6">
              <label class="form-label">Description</label>
              <input class="form-control form-control-sm" v-model="resource.storageResourceDescription" />
            </div>
            <div class="col-md-6">
              <div class="form-check">
                <input class="form-check-input" type="checkbox" id="sr-enabled" v-model="resource.enabled" />
                <label class="form-check-label" for="sr-enabled">Enabled</label>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Credentials -->
      <div class="card mb-3">
        <div class="card-body">
          <h2 class="h6 mb-3">Credentials</h2>
          <div class="row g-3">
            <div class="col-md-8">
              <label class="form-label">SSH Credential</label>
              <ssh-credential-selector v-model="selectedCredential" :null-option="false" />
            </div>
            <div class="col-md-4 d-flex align-items-end">
              <div v-if="connectionStatus === 'idle'" class="text-muted" style="font-size:0.8125rem;">
                Select a credential and test the connection.
              </div>
              <div v-else-if="connectionStatus === 'testing'" class="text-primary" style="font-size:0.8125rem;">
                <i class="fa fa-spinner fa-spin me-1"></i>Testing...
              </div>
              <div v-else-if="connectionStatus === 'connected'" class="text-success" style="font-size:0.8125rem;">
                <i class="fa fa-check-circle me-1"></i>Connected
              </div>
              <div v-else-if="connectionStatus === 'failed'" class="text-danger" style="font-size:0.8125rem;">
                <i class="fa fa-times-circle me-1"></i>{{ connectionError }}
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Save -->
      <div class="d-flex justify-content-end">
        <button class="btn btn-primary btn-sm" @click="save" :disabled="saving">
          <span v-if="saving"><i class="fa fa-spinner fa-spin me-1"></i>Saving...</span>
          <span v-else>Save Changes</span>
        </button>
      </div>
    </template>
  </div>
</template>

<script>
import { services, utils } from "django-airavata-api";
import SSHCredentialSelector from "../../../../admin/static/django_airavata_admin/src/components/credentials/SSHCredentialSelector.vue";

export default {
  name: "storage-detail-container",
  components: { "ssh-credential-selector": SSHCredentialSelector },
  props: {
    storageResourceId: { type: String, required: true },
  },
  data() {
    return {
      resource: null,
      loading: true,
      saving: false,
      selectedCredential: null,
      connectionStatus: "idle",
      connectionError: "",
      sessionId: null,
    };
  },
  methods: {
    async loadResource() {
      this.loading = true;
      try {
        this.resource = await services.StorageResourceService.retrieve({ lookup: this.storageResourceId });
      } catch (e) {
        console.error("Failed to load storage resource", e);
      }
      this.loading = false;
    },
    async save() {
      this.saving = true;
      try {
        await services.StorageResourceService.update({
          lookup: this.storageResourceId,
          data: this.resource,
        });
      } catch (e) {
        console.error("Failed to save", e);
      }
      this.saving = false;
    },
    async testConnection() {
      if (!this.selectedCredential) return;
      this.connectionStatus = "testing";
      this.connectionError = "";

      // Listen for result via SSE
      const onResult = (event) => {
        if (event.session_id === this.sessionId) {
          this.connectionStatus = event.success ? "connected" : "failed";
          this.connectionError = event.success ? "" : event.message;
          if (utils.SSEClient) utils.SSEClient.off("ssh_result", onResult);
        }
      };
      if (utils.SSEClient) utils.SSEClient.on("ssh_result", onResult);

      try {
        const res = await utils.FetchUtils.post("/api/ssh/test/", {
          hostname: this.resource.hostName,
          port: 22,
          credential_token: this.selectedCredential,
        });
        this.sessionId = res.session_id;
      } catch (e) {
        this.connectionStatus = "failed";
        this.connectionError = e.message || "Failed to start test";
        if (utils.SSEClient) utils.SSEClient.off("ssh_result", onResult);
      }
    },
    async confirmDelete() {
      if (!confirm("Delete this storage resource? This cannot be undone.")) return;
      try {
        await services.StorageResourceService.delete({ lookup: this.storageResourceId });
        window.location.href = "/resources/storage";
      } catch (e) {
        console.error("Failed to delete", e);
      }
    },
  },
  created() {
    this.loadResource();
  },
};
</script>
```

- [ ] **Step 3: Update storage list to link to detail pages**

In `UserStorageContainer.vue`, find the storage row template with `<strong>{{ storage.name }}</strong>`. Change it to link to the detail page:

Find:
```html
<strong>{{ storage.name }}</strong>
```
Replace with:
```html
<a :href="'/resources/storage/' + storage.id" class="text-decoration-none"><strong>{{ storage.name }}</strong></a>
```

- [ ] **Step 4: Build and verify**

```bash
cd /Users/yasith/code/artisan/airavata-portals/main/airavata-django-portal/django_airavata/apps/workspace
npx vite build
```

---

### Task 4: Compute Detail Page (Vue Component)

**Files:**
- Create: `django_airavata/apps/workspace/static/django_airavata_workspace/js/entry-compute-detail.js`
- Create: `django_airavata/apps/workspace/static/django_airavata_workspace/js/containers/ComputeDetailContainer.vue`

- [ ] **Step 1: Create entry point**

Create `entry-compute-detail.js`:
```javascript
import { h } from "vue";
import { components, entry } from "django-airavata-common-ui";
import ComputeDetailContainer from "./containers/ComputeDetailContainer.vue";

entry(({ createApp }) => {
  const el = document.getElementById("compute-detail");
  const computeResourceId = el ? el.dataset.computeResourceId : null;
  const app = createApp({
    render() {
      return h(components.MainLayout, null, {
        default: () => h(ComputeDetailContainer, { computeResourceId }),
      });
    },
  });
  app.mount("#compute-detail");
});
```

- [ ] **Step 2: Create ComputeDetailContainer.vue**

Create `containers/ComputeDetailContainer.vue`:
```vue
<template>
  <div>
    <div class="mb-2">
      <a href="/resources/compute" class="text-muted" style="font-size:0.8125rem;">
        <i class="fa fa-arrow-left me-1"></i>Back to compute list
      </a>
    </div>

    <div v-if="loading" class="text-center py-4 text-muted">
      <i class="fa fa-spinner fa-spin me-1"></i> Loading...
    </div>

    <template v-if="resource">
      <!-- Header -->
      <div class="d-flex align-items-center justify-content-between mb-3">
        <div>
          <h1 class="h4 mb-0">{{ resource.hostName }}</h1>
          <span class="badge" :class="resource.enabled ? 'bg-success' : 'bg-secondary'">
            {{ resource.enabled ? 'Enabled' : 'Disabled' }}
          </span>
        </div>
        <div class="d-flex gap-2">
          <button class="btn btn-primary btn-sm" @click="testConnection" :disabled="!selectedCredential || connectionStatus === 'testing'">
            <i class="fa fa-plug me-1"></i>Test Connection
          </button>
          <button class="btn btn-outline-danger btn-sm" @click="confirmDelete">
            <i class="fa fa-trash me-1"></i>Delete
          </button>
        </div>
      </div>

      <!-- General -->
      <div class="card mb-3">
        <div class="card-body">
          <h2 class="h6 mb-3">General</h2>
          <div class="row g-3">
            <div class="col-md-6">
              <label class="form-label">Host Name <span class="text-danger">*</span></label>
              <input class="form-control form-control-sm" v-model="resource.hostName" />
            </div>
            <div class="col-md-6">
              <label class="form-label">Description</label>
              <input class="form-control form-control-sm" v-model="resource.resourceDescription" />
            </div>
            <div class="col-md-3">
              <label class="form-label">CPUs Per Node</label>
              <input class="form-control form-control-sm" type="number" v-model.number="resource.cpusPerNode" />
            </div>
            <div class="col-md-3">
              <label class="form-label">Max Memory (MB)</label>
              <input class="form-control form-control-sm" type="number" v-model.number="resource.maxMemoryPerNode" />
            </div>
            <div class="col-md-2">
              <label class="form-label">Default Nodes</label>
              <input class="form-control form-control-sm" type="number" v-model.number="resource.defaultNodeCount" />
            </div>
            <div class="col-md-2">
              <label class="form-label">Default CPUs</label>
              <input class="form-control form-control-sm" type="number" v-model.number="resource.defaultCPUCount" />
            </div>
            <div class="col-md-2">
              <label class="form-label">Default Walltime (min)</label>
              <input class="form-control form-control-sm" type="number" v-model.number="resource.defaultWalltime" />
            </div>
            <div class="col-md-6">
              <div class="form-check">
                <input class="form-check-input" type="checkbox" id="cr-enabled" v-model="resource.enabled" />
                <label class="form-check-label" for="cr-enabled">Enabled</label>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Credentials -->
      <div class="card mb-3">
        <div class="card-body">
          <h2 class="h6 mb-3">Credentials</h2>
          <div class="row g-3">
            <div class="col-md-6">
              <label class="form-label">SSH Credential</label>
              <ssh-credential-selector v-model="selectedCredential" :null-option="false" />
            </div>
            <div class="col-md-3 d-flex align-items-end">
              <div v-if="connectionStatus === 'idle'" class="text-muted" style="font-size:0.8125rem;">Not tested</div>
              <div v-else-if="connectionStatus === 'testing'" class="text-primary" style="font-size:0.8125rem;">
                <i class="fa fa-spinner fa-spin me-1"></i>Testing...
              </div>
              <div v-else-if="connectionStatus === 'connected'" class="text-success" style="font-size:0.8125rem;">
                <i class="fa fa-check-circle me-1"></i>Connected
              </div>
              <div v-else-if="connectionStatus === 'failed'" class="text-danger" style="font-size:0.8125rem;">
                <i class="fa fa-times-circle me-1"></i>{{ connectionError }}
              </div>
            </div>
            <div class="col-md-3 d-flex align-items-end">
              <button v-if="connectionStatus === 'connected'" class="btn btn-outline-primary btn-sm"
                @click="discoverHpcInfo" :disabled="discovering">
                <i class="fa fa-search me-1"></i>{{ discovering ? 'Discovering...' : 'Discover HPC Info' }}
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- HPC Configuration -->
      <div class="card mb-3">
        <div class="card-body">
          <div class="d-flex align-items-center justify-content-between mb-3">
            <h2 class="h6 mb-0">HPC Configuration</h2>
            <button class="btn btn-outline-secondary btn-sm" @click="addPartition">
              <i class="fa fa-plus me-1"></i>Add Partition
            </button>
          </div>
          <table class="table table-hover">
            <thead>
              <tr>
                <th>Partition</th>
                <th>Nodes</th>
                <th>CPUs</th>
                <th>Memory (MB)</th>
                <th>GPUs</th>
                <th>GPU Types</th>
                <th>Accounts</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="partitions.length === 0">
                <td colspan="8">
                  <div class="table-empty">
                    <i class="fa fa-th-list table-empty__icon"></i>
                    <div class="table-empty__title">No partitions configured</div>
                    <div class="table-empty__text">Use "Discover HPC Info" to auto-detect, or add manually.</div>
                  </div>
                </td>
              </tr>
              <tr v-for="(p, idx) in partitions" :key="idx">
                <td><input class="form-control form-control-sm" v-model="p.partition" /></td>
                <td><input class="form-control form-control-sm" type="number" v-model.number="p.nodes" style="width:70px;" /></td>
                <td><input class="form-control form-control-sm" type="number" v-model.number="p.maxCpusPerNode" style="width:70px;" /></td>
                <td><input class="form-control form-control-sm" type="number" v-model.number="p.maxMemMbPerNode" style="width:90px;" /></td>
                <td><input class="form-control form-control-sm" type="number" v-model.number="p.maxGpusPerNode" style="width:60px;" /></td>
                <td><input class="form-control form-control-sm" v-model="p.gpuTypes" style="width:100px;" /></td>
                <td><input class="form-control form-control-sm" v-model="p.accounts" style="width:100px;" /></td>
                <td>
                  <a href="#" class="action-link text-danger" @click.prevent="partitions.splice(idx, 1)">
                    <i class="fa fa-trash"></i>
                  </a>
                </td>
              </tr>
            </tbody>
          </table>
          <div v-if="partitions.length > 0" class="text-end text-muted" style="font-size:0.75rem; padding: 6px 8px;">Showing {{ partitions.length }}</div>
        </div>
      </div>

      <!-- Job Submission -->
      <div class="card mb-3">
        <div class="card-body">
          <h2 class="h6 mb-3">Job Submission</h2>
          <div class="row g-3">
            <div class="col-md-4">
              <label class="form-label">Resource Manager</label>
              <select class="form-select form-select-sm" v-model="jobSubmission.resourceManager">
                <option value="SLURM">SLURM</option>
                <option value="PBS">PBS</option>
                <option value="SGE">SGE</option>
                <option value="FORK">FORK</option>
              </select>
            </div>
            <div class="col-md-4">
              <label class="form-label">SSH Port</label>
              <input class="form-control form-control-sm" type="number" v-model.number="jobSubmission.sshPort" />
            </div>
            <div class="col-md-4">
              <label class="form-label">Alternative SSH Host</label>
              <input class="form-control form-control-sm" v-model="jobSubmission.alternativeHost" placeholder="Optional" />
            </div>
          </div>
        </div>
      </div>

      <!-- Save -->
      <div class="d-flex justify-content-end">
        <button class="btn btn-primary btn-sm" @click="save" :disabled="saving">
          <span v-if="saving"><i class="fa fa-spinner fa-spin me-1"></i>Saving...</span>
          <span v-else>Save Changes</span>
        </button>
      </div>
    </template>
  </div>
</template>

<script>
import { services, utils } from "django-airavata-api";
import SSHCredentialSelector from "../../../../admin/static/django_airavata_admin/src/components/credentials/SSHCredentialSelector.vue";

export default {
  name: "compute-detail-container",
  components: { "ssh-credential-selector": SSHCredentialSelector },
  props: {
    computeResourceId: { type: String, required: true },
  },
  data() {
    return {
      resource: null,
      loading: true,
      saving: false,
      selectedCredential: null,
      connectionStatus: "idle",
      connectionError: "",
      sessionId: null,
      discovering: false,
      partitions: [],
      jobSubmission: {
        resourceManager: "SLURM",
        sshPort: 22,
        alternativeHost: "",
      },
    };
  },
  methods: {
    async loadResource() {
      this.loading = true;
      try {
        this.resource = await services.ComputeResourceService.retrieve({ lookup: this.computeResourceId });
        if (this.resource.batchQueues) {
          this.partitions = this.resource.batchQueues.map((q) => ({
            partition: q.queueName || "",
            nodes: q.maxNodes || 0,
            maxCpusPerNode: q.maxProcessors || 0,
            maxMemMbPerNode: q.maxMemory || 0,
            maxGpusPerNode: 0,
            gpuTypes: "",
            accounts: "",
          }));
        }
      } catch (e) {
        console.error("Failed to load compute resource", e);
      }
      this.loading = false;
    },
    async save() {
      this.saving = true;
      try {
        await services.ComputeResourceService.update({
          lookup: this.computeResourceId,
          data: this.resource,
        });
      } catch (e) {
        console.error("Failed to save", e);
      }
      this.saving = false;
    },
    async testConnection() {
      if (!this.selectedCredential) return;
      this.connectionStatus = "testing";
      this.connectionError = "";

      const onResult = (event) => {
        if (event.session_id === this.sessionId) {
          this.connectionStatus = event.success ? "connected" : "failed";
          this.connectionError = event.success ? "" : event.message;
          if (utils.SSEClient) utils.SSEClient.off("ssh_result", onResult);
        }
      };
      if (utils.SSEClient) utils.SSEClient.on("ssh_result", onResult);

      try {
        const res = await utils.FetchUtils.post("/api/ssh/test/", {
          hostname: this.resource.hostName,
          port: this.jobSubmission.sshPort || 22,
          credential_token: this.selectedCredential,
        });
        this.sessionId = res.session_id;
      } catch (e) {
        this.connectionStatus = "failed";
        this.connectionError = e.message || "Failed to start test";
        if (utils.SSEClient) utils.SSEClient.off("ssh_result", onResult);
      }
    },
    async discoverHpcInfo() {
      if (!this.sessionId) return;
      this.discovering = true;
      try {
        const res = await utils.FetchUtils.post("/api/ssh/run-info/", {
          session_id: this.sessionId,
        });
        if (res.partitions && res.partitions.length > 0) {
          this.partitions = res.partitions.map((p) => ({
            partition: p.partition,
            nodes: p.nodes,
            maxCpusPerNode: p.maxCpusPerNode,
            maxMemMbPerNode: p.maxMemMbPerNode,
            maxGpusPerNode: p.maxGpusPerNode,
            gpuTypes: (p.gpuTypes || []).join(","),
            accounts: (p.accounts || []).join(","),
          }));
        }
      } catch (e) {
        console.error("HPC discovery failed", e);
      }
      this.discovering = false;
    },
    addPartition() {
      this.partitions.push({
        partition: "", nodes: 0, maxCpusPerNode: 0, maxMemMbPerNode: 0,
        maxGpusPerNode: 0, gpuTypes: "", accounts: "",
      });
    },
    async confirmDelete() {
      if (!confirm("Delete this compute resource? This cannot be undone.")) return;
      try {
        await services.ComputeResourceService.delete({ lookup: this.computeResourceId });
        window.location.href = "/resources/compute";
      } catch (e) {
        console.error("Failed to delete", e);
      }
    },
  },
  created() {
    this.loadResource();
  },
};
</script>
```

- [ ] **Step 3: Update compute list to link to detail pages**

In `ComputeContainer.vue`, find `<strong>{{ resource.name }}</strong>`. Change to:
```html
<a :href="'/resources/compute/' + resource.id" class="text-decoration-none"><strong>{{ resource.name }}</strong></a>
```

- [ ] **Step 4: Build and verify**

```bash
cd /Users/yasith/code/artisan/airavata-portals/main/airavata-django-portal/django_airavata/apps/workspace
npx vite build
```

---

### Task 5: Gateway Settings (Functional)

**Files:**
- Modify: `django_airavata/apps/workspace/static/django_airavata_workspace/js/containers/GatewaySettingsContainer.vue`

- [ ] **Step 1: Rewrite GatewaySettingsContainer.vue to load/save real data**

Replace the entire content of `GatewaySettingsContainer.vue` with:

```vue
<template>
  <div>
    <div class="row align-items-center mb-3">
      <div class="col">
        <h1 class="h4 mb-0">Gateway Settings</h1>
        <p class="text-muted mb-0">Configure portal-wide settings for all users.</p>
      </div>
    </div>

    <div v-if="loading" class="text-center py-4 text-muted">
      <i class="fa fa-spinner fa-spin me-1"></i> Loading settings...
    </div>

    <template v-if="!loading">
      <!-- General -->
      <div class="card mb-3">
        <div class="card-body">
          <h2 class="h6 mb-3">General</h2>
          <div class="row g-3">
            <div class="col-md-6">
              <label class="form-label">Gateway ID</label>
              <input class="form-control form-control-sm" :value="gatewayId" disabled />
              <div class="form-text">Read-only identifier for this gateway.</div>
            </div>
            <div class="col-md-6">
              <label class="form-label">Portal Title</label>
              <input class="form-control form-control-sm" :value="portalTitle" disabled />
              <div class="form-text">Set in settings_local.py as PORTAL_TITLE.</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Default Storage -->
      <div class="card mb-3">
        <div class="card-body">
          <h2 class="h6 mb-3">Default Storage</h2>
          <div class="row g-3">
            <div class="col-md-4">
              <label class="form-label">Storage Resource</label>
              <select class="form-select form-select-sm" v-model="selectedStorageId">
                <option :value="null">None</option>
                <option v-for="(name, id) in storageResources" :key="id" :value="id">{{ name }}</option>
              </select>
            </div>
            <div class="col-md-4">
              <label class="form-label">File System Root</label>
              <input class="form-control form-control-sm" v-model="fsRoot" placeholder="/home/user/storage" />
            </div>
            <div class="col-md-4">
              <label class="form-label">Login Username</label>
              <input class="form-control form-control-sm" v-model="loginUsername" placeholder="airavata" />
            </div>
          </div>
        </div>
      </div>

      <!-- Default Credential -->
      <div class="card mb-3">
        <div class="card-body">
          <h2 class="h6 mb-3">Default SSH Credential</h2>
          <div class="row g-3">
            <div class="col-md-6">
              <ssh-credential-selector v-model="selectedCredentialToken" :null-option="true" />
            </div>
          </div>
        </div>
      </div>

      <!-- Appearance (read-only) -->
      <div class="card mb-3">
        <div class="card-body">
          <h2 class="h6 mb-3">Appearance</h2>
          <p class="text-muted mb-0" style="font-size:0.8125rem;">
            Theme and branding settings are configured in <code>settings_local.py</code>.
          </p>
        </div>
      </div>

      <!-- Save -->
      <div class="d-flex justify-content-end">
        <button class="btn btn-primary btn-sm" @click="saveSettings" :disabled="saving">
          <span v-if="saving"><i class="fa fa-spinner fa-spin me-1"></i>Saving...</span>
          <span v-else>Save Settings</span>
        </button>
      </div>
    </template>
  </div>
</template>

<script>
import { services, utils } from "django-airavata-api";
import SSHCredentialSelector from "../../../../admin/static/django_airavata_admin/src/components/credentials/SSHCredentialSelector.vue";

export default {
  name: "gateway-settings-container",
  components: { "ssh-credential-selector": SSHCredentialSelector },
  data() {
    return {
      loading: true,
      saving: false,
      gatewayId: "",
      portalTitle: "",
      storageResources: {},
      selectedStorageId: null,
      fsRoot: "",
      loginUsername: "",
      selectedCredentialToken: null,
      gatewayProfile: null,
    };
  },
  methods: {
    async loadSettings() {
      this.loading = true;

      // Read gateway ID and portal title from the page context
      const el = document.getElementById("gateway-settings");
      this.gatewayId = el?.dataset?.gatewayId || "";
      this.portalTitle = el?.dataset?.portalTitle || "";

      try {
        // Load storage resource names
        this.storageResources = await services.StorageResourceService.names();
      } catch { this.storageResources = {}; }

      try {
        // Load gateway resource profile
        const profile = await utils.FetchUtils.get("/api/gateway-resource-profile/");
        this.gatewayProfile = profile;

        // Extract first storage preference if present
        if (profile.storagePreferences && profile.storagePreferences.length > 0) {
          const pref = profile.storagePreferences[0];
          this.selectedStorageId = pref.storageResourceId || null;
          this.fsRoot = pref.fileSystemRootLocation || "";
          this.loginUsername = pref.loginUserName || "";
          this.selectedCredentialToken = pref.resourceSpecificCredentialStoreToken || null;
        }
      } catch (e) {
        console.error("Failed to load gateway profile", e);
      }

      this.loading = false;
    },
    async saveSettings() {
      this.saving = true;
      try {
        // Update gateway profile storage preferences
        const updatedProfile = { ...this.gatewayProfile };
        if (this.selectedStorageId) {
          updatedProfile.storagePreferences = [{
            storageResourceId: this.selectedStorageId,
            fileSystemRootLocation: this.fsRoot,
            loginUserName: this.loginUsername,
            resourceSpecificCredentialStoreToken: this.selectedCredentialToken,
          }];
        } else {
          updatedProfile.storagePreferences = [];
        }

        await utils.FetchUtils.put("/api/gateway-resource-profile/", updatedProfile);
      } catch (e) {
        console.error("Failed to save settings", e);
      }
      this.saving = false;
    },
  },
  created() {
    this.loadSettings();
  },
};
</script>
```

- [ ] **Step 2: Update the gateway settings view to pass context data**

In `django_airavata/apps/workspace/views.py`, update the `gateway_settings` view to pass `gateway_id` and `portal_title` as template context:

```python
@login_required
def gateway_settings(request):
    request.active_nav_item = "settings"
    return render(
        request,
        "django_airavata_workspace/base.html",
        {
            "bundle_name": "gateway-settings",
            "entry_point": ENTRY_POINTS["gateway-settings"],
            "gateway_id": settings.GATEWAY_ID,
            "portal_title": getattr(settings, "PORTAL_TITLE", "Airavata Portal"),
        },
    )
```

Also update the base template to pass these as data attributes. In `django_airavata/apps/workspace/templates/django_airavata_workspace/base.html`, update the div to also handle gateway settings context:

```html
<div id="{{ bundle_name }}" {% if storage_resource_id %}data-storage-resource-id="{{ storage_resource_id }}"{% endif %} {% if compute_resource_id %}data-compute-resource-id="{{ compute_resource_id }}"{% endif %} {% if gateway_id %}data-gateway-id="{{ gateway_id }}"{% endif %} {% if portal_title %}data-portal-title="{{ portal_title }}"{% endif %}></div>
```

- [ ] **Step 3: Build and verify**

```bash
cd /Users/yasith/code/artisan/airavata-portals/main/airavata-django-portal/django_airavata/apps/workspace
npx vite build
```

---

### Task 6: Build All and Manual Verification

**Files:** None (verification only)

- [ ] **Step 1: Build all bundles**

```bash
cd /Users/yasith/code/artisan/airavata-portals/main/airavata-django-portal
cd django_airavata/apps/api && npx vite build
cd ../../static/common && npx vite build
cd ../../apps/workspace && npx vite build
cd ../admin && npx vite build
```

- [ ] **Step 2: Restart Django**

```bash
touch django_airavata/urls.py
```

- [ ] **Step 3: Verify storage detail page**

Navigate to `http://localhost:8000/resources/storage`, click on "localhost" resource name.
Expected: Detail page loads at `/resources/storage/<id>` with General and Credentials cards, Save button.

- [ ] **Step 4: Verify compute detail page**

Navigate to `http://localhost:8000/resources/compute`, register a test resource, click its name.
Expected: Detail page loads with General, Credentials, HPC Configuration, and Job Submission cards.

- [ ] **Step 5: Verify gateway settings**

Navigate to `http://localhost:8000/gateway/settings`.
Expected: Shows Gateway ID, Portal Title (read-only), Default Storage dropdown (populated), SSH credential selector, File System Root. Save persists.
