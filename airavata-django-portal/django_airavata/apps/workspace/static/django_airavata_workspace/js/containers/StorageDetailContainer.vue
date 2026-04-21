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
            {{ resource.host_name }}
            <span v-if="resource.enabled" class="badge bg-success ms-2" style="font-size: 0.75rem"
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
                v-model="resource.host_name"
                type="text"
                class="form-control form-control-sm"
              />
            </div>
            <div class="col-md-6">
              <label class="form-label">Description</label>
              <input
                v-model="resource.storage_resource_description"
                type="text"
                class="form-control form-control-sm"
                placeholder="Optional description"
              />
            </div>
            <div class="col-12">
              <div class="form-check form-switch">
                <input
                  id="enabledToggle"
                  v-model="resource.enabled"
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
          :disabled="saving || !resource.host_name"
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

<script>
import { services, utils } from "django-airavata-api";
import SSHCredentialSelector from "../../../../../admin/static/django_airavata_admin/src/components/credentials/SSHCredentialSelector.vue";

export default {
  name: "StorageDetailContainer",
  components: {
    "ssh-credential-selector": SSHCredentialSelector,
  },
  props: {
    storageResourceId: {
      type: String,
      default: null,
    },
  },
  data() {
    return {
      loading: true,
      resource: null,
      credentialToken: null,
      saving: false,
      testing: false,
      testStatus: null,
      sseUnsubscribers: [],
    };
  },
  created() {
    if (this.storageResourceId) {
      this.loadResource();
    } else {
      this.loading = false;
    }
    if (utils.SSEClient) {
      utils.SSEClient.on("ssh_result", this.onSshResult);
    }
  },
  beforeUnmount() {
    if (utils.SSEClient) {
      utils.SSEClient.off("ssh_result", this.onSshResult);
    }
  },
  methods: {
    async loadResource() {
      this.loading = true;
      try {
        this.resource = await services.StorageResourceService.retrieve({
          lookup: this.storageResourceId,
        });
      } catch {
        this.resource = null;
      }
      this.loading = false;
    },
    async save() {
      if (!this.resource.host_name) return;
      this.saving = true;
      try {
        await services.StorageResourceService.update({
          lookup: this.storageResourceId,
          data: this.resource,
        });
      } catch (e) {
        window.alert(e?.message || "Failed to save storage resource.");
      }
      this.saving = false;
    },
    async testConnection() {
      this.testing = true;
      this.testStatus = null;
      try {
        await utils.FetchUtils.post("/api/ssh/test/", {
          resource_id: this.storageResourceId,
          credential_token: this.credentialToken,
        });
      } catch (e) {
        this.testing = false;
        this.testStatus = {
          success: false,
          message: e?.message || "Failed to initiate connection test.",
        };
      }
    },
    onSshResult(event) {
      this.testing = false;
      this.testStatus = {
        success: event.success,
        message: event.message,
      };
    },
    async confirmDelete() {
      if (
        !window.confirm(
          `Delete storage resource "${this.resource.host_name}"? This action cannot be undone.`,
        )
      )
        return;
      try {
        await services.StorageResourceService.delete({ lookup: this.storageResourceId });
        window.location.href = "/resources/storage";
      } catch (e) {
        window.alert(e?.message || "Failed to delete storage resource.");
      }
    },
  },
};
</script>
