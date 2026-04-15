<template>
  <div>
    <div class="row align-items-center mb-3">
      <div class="col">
        <h1 class="h4 mb-0">Gateway Settings</h1>
        <p class="text-muted mb-0">Configure portal-wide settings for all users.</p>
      </div>
    </div>

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
            <div class="form-text">Set in settings_local.py.</div>
          </div>
        </div>
      </div>
    </div>

    <div class="card mb-3">
      <div class="card-body">
        <h2 class="h6 mb-3">Default Storage</h2>
        <div class="row g-3">
          <div class="col-md-6">
            <label class="form-label">Storage Resource</label>
            <select class="form-select form-select-sm" v-model="storageResourceId">
              <option :value="null">None</option>
              <option v-for="(name, id) in storageResources" :key="id" :value="id">{{ name }}</option>
            </select>
          </div>
          <div class="col-md-6">
            <label class="form-label">SSH Credential</label>
            <ssh-credential-selector v-model="resourceSpecificCredentialStoreToken" />
          </div>
          <div class="col-md-6">
            <label class="form-label">Login Username</label>
            <input class="form-control form-control-sm" v-model="loginUserName" placeholder="username" />
          </div>
          <div class="col-md-6">
            <label class="form-label">File System Root Location</label>
            <input class="form-control form-control-sm" v-model="fileSystemRootLocation" placeholder="/home/user/storage" />
          </div>
        </div>
      </div>
    </div>

    <div v-if="isGatewayAdmin" class="card mb-3">
      <div class="card-body">
        <div class="d-flex align-items-center mb-3">
          <h2 class="h6 mb-0 flex-grow-1">Advanced Settings</h2>
          <button
            class="btn btn-primary btn-sm"
            @click="saveLocalSettings"
            :disabled="localSettingsSaving || localSettingsLoading"
          >
            <span v-if="localSettingsSaving"><i class="fa fa-spinner fa-spin me-1"></i>Saving...</span>
            <span v-else>Save</span>
          </button>
        </div>
        <p class="text-muted small mb-2">
          Edit <code>django_airavata/settings_local.py</code> directly. Changes take effect after the portal restarts.
          <strong class="text-danger">Warning:</strong> this file executes as Python on startup &mdash; mistakes can break the portal.
        </p>
        <div v-if="localSettingsLoading" class="text-muted small">
          <i class="fa fa-spinner fa-spin me-1"></i>Loading settings_local.py...
        </div>
        <textarea
          v-else
          v-model="localSettingsContent"
          rows="20"
          class="form-control"
          spellcheck="false"
          style="font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; font-size: 12px; white-space: pre; tab-size: 4;"
        ></textarea>
        <div v-if="localSettingsMessage" :class="['small', 'mt-2', localSettingsError ? 'text-danger' : 'text-success']">
          {{ localSettingsMessage }}
        </div>
      </div>
    </div>

    <div class="d-flex justify-content-end">
      <button class="btn btn-primary btn-sm" @click="saveSettings" :disabled="saving">
        <span v-if="saving"><i class="fa fa-spinner fa-spin me-1"></i>Saving...</span>
        <span v-else>Save Settings</span>
      </button>
    </div>
  </div>
</template>

<script>
import { services, utils } from "django-airavata-api";
import SSHCredentialSelector from "../../../../../admin/static/django_airavata_admin/src/components/credentials/SSHCredentialSelector.vue";

export default {
  name: "gateway-settings-container",
  components: {
    "ssh-credential-selector": SSHCredentialSelector,
  },
  data() {
    return {
      saving: false,
      gatewayId: "",
      portalTitle: "",
      storageResources: {},
      gatewayResourceProfile: null,
      // Storage preference fields
      storageResourceId: null,
      fileSystemRootLocation: "",
      loginUserName: "",
      resourceSpecificCredentialStoreToken: null,
      // Advanced settings (settings_local.py editor)
      isGatewayAdmin: false,
      localSettingsContent: "",
      localSettingsLoading: false,
      localSettingsSaving: false,
      localSettingsMessage: "",
      localSettingsError: false,
    };
  },
  methods: {
    async loadSettings() {
      const el = document.getElementById("gateway-settings");
      if (el) {
        this.gatewayId = el.dataset.gatewayId || "";
        this.portalTitle = el.dataset.portalTitle || "";
        this.isGatewayAdmin = el.dataset.isGatewayAdmin === "true";
      }
      if (this.isGatewayAdmin) {
        this.loadLocalSettings();
      }

      try {
        this.storageResources = await services.StorageResourceService.names();
      } catch {
        this.storageResources = {};
      }

      try {
        const profile = await utils.FetchUtils.get("/api/gateway-resource-profile/");
        this.gatewayResourceProfile = profile;
        if (!this.gatewayId && profile && profile.gateway_id) {
          this.gatewayId = profile.gateway_id;
        }
        const pref =
          profile.storage_preferences && profile.storage_preferences.length > 0
            ? profile.storage_preferences[0]
            : null;
        if (pref) {
          this.storageResourceId = pref.storage_resource_id || null;
          this.fileSystemRootLocation = pref.file_system_root_location || "";
          this.loginUserName = pref.login_user_name || "";
          this.resourceSpecificCredentialStoreToken =
            pref.resource_specific_credential_store_token || null;
        }
      } catch {
        this.gatewayResourceProfile = null;
      }
    },
    async saveSettings() {
      this.saving = true;
      try {
        const updatedPref = {
          storage_resource_id: this.storageResourceId,
          file_system_root_location: this.fileSystemRootLocation,
          login_user_name: this.loginUserName,
          resource_specific_credential_store_token:
            this.resourceSpecificCredentialStoreToken,
        };
        const existingPrefs =
          this.gatewayResourceProfile &&
          this.gatewayResourceProfile.storage_preferences
            ? this.gatewayResourceProfile.storage_preferences.slice(1)
            : [];
        const updatedProfile = Object.assign({}, this.gatewayResourceProfile, {
          storage_preferences: [updatedPref, ...existingPrefs],
        });
        await utils.FetchUtils.put("/api/gateway-resource-profile/", updatedProfile);
        this.gatewayResourceProfile = updatedProfile;
      } finally {
        this.saving = false;
      }
    },
    async loadLocalSettings() {
      this.localSettingsLoading = true;
      this.localSettingsMessage = "";
      this.localSettingsError = false;
      try {
        const data = await utils.FetchUtils.get("/api/settings/local/");
        this.localSettingsContent = data && data.content ? data.content : "";
      } catch (e) {
        this.localSettingsError = true;
        this.localSettingsMessage =
          "Failed to load settings_local.py: " + (e && e.message ? e.message : e);
      } finally {
        this.localSettingsLoading = false;
      }
    },
    async saveLocalSettings() {
      this.localSettingsSaving = true;
      this.localSettingsMessage = "";
      this.localSettingsError = false;
      try {
        await utils.FetchUtils.post("/api/settings/local/", {
          content: this.localSettingsContent,
        });
        this.localSettingsMessage =
          "Saved! Restart the portal for changes to take effect.";
      } catch (e) {
        this.localSettingsError = true;
        this.localSettingsMessage =
          "Failed to save settings_local.py: " + (e && e.message ? e.message : e);
      } finally {
        this.localSettingsSaving = false;
      }
    },
  },
  created() {
    this.loadSettings();
  },
};
</script>
