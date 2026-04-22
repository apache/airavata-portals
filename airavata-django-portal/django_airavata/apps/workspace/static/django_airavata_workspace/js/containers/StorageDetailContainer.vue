<template>
  <div>
    <div class="mb-3">
      <a href="/resources/storage" class="text-muted" style="font-size: 0.8125rem">
        <i class="fa fa-arrow-left me-1"></i>Back to storage list
      </a>
    </div>

    <div v-if="loading" class="text-center py-5 text-muted">
      <i class="fa fa-spinner fa-spin me-1"></i> Loading storage resource...
    </div>

    <template v-else-if="resource">
      <!-- Header -->
      <div class="row align-items-center mb-3">
        <div class="col">
          <h1 class="h4 mb-0">
            {{ (resource as Record<string, unknown>).host_name }}
            <span v-if="(resource as Record<string, unknown>).enabled" class="badge bg-success ms-2" style="font-size: 0.75rem"
              >Enabled</span
            >
            <span v-else class="badge bg-secondary ms-2" style="font-size: 0.75rem">Disabled</span>
          </h1>
        </div>
        <div class="col-auto d-flex gap-2">
          <a
            :href="'/resources/storage/' + storageResourceId + '/tree'"
            class="btn btn-primary btn-sm"
          >
            <i class="fa fa-folder-open me-1"></i>View Files
          </a>
          <button
            class="btn btn-outline-secondary btn-sm"
            :disabled="testing"
            @click="testConnection"
          >
            <span v-if="testing"><i class="fa fa-spinner fa-spin me-1"></i>Testing...</span>
            <span v-else><i class="fa fa-plug me-1"></i>Test Connection</span>
          </button>
          <button class="btn btn-outline-danger btn-sm" @click="confirmDelete">
            <i class="fa fa-trash me-1"></i>Delete
          </button>
        </div>
      </div>

      <!-- Test connection status -->
      <div
        v-if="testStatus"
        class="alert mb-3"
        :class="testStatus.success ? 'alert-success' : 'alert-danger'"
        style="font-size: 0.875rem"
      >
        <i
          :class="testStatus.success ? 'fa fa-check-circle' : 'fa fa-times-circle'"
          class="me-1"
        ></i>
        {{ testStatus.message }}
        <button
          type="button"
          class="btn-close float-end"
          style="font-size: 0.75rem"
          @click="testStatus = null"
        ></button>
      </div>

      <!-- Card 1: General -->
      <div class="card mb-3">
        <div class="card-body">
          <h6 class="mb-3">General</h6>
          <div class="row g-3">
            <div class="col-md-6">
              <label class="form-label">Host Name <span class="text-danger">*</span></label>
              <input
                v-model="(resource as Record<string, unknown>).host_name"
                type="text"
                class="form-control form-control-sm"
              />
            </div>
            <div class="col-md-6">
              <label class="form-label">Description</label>
              <input
                v-model="(resource as Record<string, unknown>).storage_resource_description"
                type="text"
                class="form-control form-control-sm"
                placeholder="Optional description"
              />
            </div>
            <div class="col-12">
              <div class="form-check form-switch">
                <input
                  id="enabledToggle"
                  v-model="(resource as Record<string, unknown>).enabled"
                  class="form-check-input"
                  type="checkbox"
                />
                <label class="form-check-label" for="enabledToggle">Enabled</label>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Card 2: Credentials -->
      <div class="card mb-3">
        <div class="card-body">
          <h6 class="mb-3">Credentials</h6>
          <div class="row g-3">
            <div class="col-md-8">
              <label class="form-label">SSH Credential</label>
              <ssh-credential-selector v-model="credentialToken" :null-option="true" />
            </div>
          </div>
        </div>
      </div>

      <!-- Save button -->
      <div class="d-flex justify-content-end">
        <button
          class="btn btn-primary btn-sm"
          :disabled="saving || !(resource as Record<string, unknown>).host_name"
          @click="save"
        >
          <span v-if="saving"><i class="fa fa-spinner fa-spin me-1"></i>Saving...</span>
          <span v-else><i class="fa fa-save me-1"></i>Save</span>
        </button>
      </div>
    </template>

    <div v-else class="alert alert-danger">Failed to load storage resource.</div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from "vue";
import { services, utils } from "django-airavata-api";
import SshCredentialSelector from "../../../../../admin/static/django_airavata_admin/src/components/credentials/SSHCredentialSelector.vue";

interface TestStatus {
  success: boolean;
  message: string;
}

interface SshResultEvent {
  success: boolean;
  message: string;
}

const props = withDefaults(defineProps<{
  storageResourceId?: string | null;
}>(), {
  storageResourceId: null,
});

const loading = ref(true);
const resource = ref<unknown>(null);
const credentialToken = ref<string | null>(null);
const saving = ref(false);
const testing = ref(false);
const testStatus = ref<TestStatus | null>(null);

function onSshResult(event: SshResultEvent): void {
  testing.value = false;
  testStatus.value = {
    success: event.success,
    message: event.message,
  };
}

async function loadResource(): Promise<void> {
  loading.value = true;
  try {
    resource.value = await services.StorageResourceService.retrieve({
      lookup: props.storageResourceId,
    });
  } catch {
    resource.value = null;
  }
  loading.value = false;
}

async function save(): Promise<void> {
  const res = resource.value as Record<string, unknown>;
  if (!res.host_name) return;
  saving.value = true;
  try {
    await services.StorageResourceService.update({
      lookup: props.storageResourceId,
      data: resource.value,
    });
  } catch (e) {
    const err = e as { message?: string };
    window.alert(err?.message || "Failed to save storage resource.");
  }
  saving.value = false;
}

async function testConnection(): Promise<void> {
  testing.value = true;
  testStatus.value = null;
  try {
    await (utils.FetchUtils as unknown as { post(_url: string, _data: unknown): Promise<unknown> }).post("/api/ssh/test/", {
      resource_id: props.storageResourceId,
      credential_token: credentialToken.value,
    });
  } catch (e) {
    testing.value = false;
    const err = e as { message?: string };
    testStatus.value = {
      success: false,
      message: err?.message || "Failed to initiate connection test.",
    };
  }
}

async function confirmDelete(): Promise<void> {
  const res = resource.value as Record<string, unknown>;
  if (
    !window.confirm(
      `Delete storage resource "${res.host_name}"? This action cannot be undone.`,
    )
  )
    return;
  try {
    await services.StorageResourceService.delete({ lookup: props.storageResourceId });
    window.location.href = "/resources/storage";
  } catch (e) {
    const err = e as { message?: string };
    window.alert(err?.message || "Failed to delete storage resource.");
  }
}

onMounted(() => {
  if (props.storageResourceId) {
    loadResource();
  } else {
    loading.value = false;
  }
  if ((utils as unknown as Record<string, unknown>).SSEClient) {
    (utils as unknown as { SSEClient: { on(_event: string, _handler: (_e: SshResultEvent) => void): void } }).SSEClient.on("ssh_result", onSshResult);
  }
});

onBeforeUnmount(() => {
  if ((utils as unknown as Record<string, unknown>).SSEClient) {
    (utils as unknown as { SSEClient: { off(_event: string, _handler: (_e: SshResultEvent) => void): void } }).SSEClient.off("ssh_result", onSshResult);
  }
});
</script>
