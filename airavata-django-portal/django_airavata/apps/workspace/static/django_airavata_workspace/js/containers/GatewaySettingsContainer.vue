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
            <label class="form-label">File System Root Location</label>
            <input class="form-control form-control-sm" v-model="fileSystemRootLocation" placeholder="/home/user/storage" />
          </div>
          <div class="col-md-6">
            <label class="form-label">Login Username</label>
            <input class="form-control form-control-sm" v-model="loginUserName" placeholder="username" />
          </div>
        </div>
      </div>
    </div>

    <div class="card mb-3">
      <div class="card-body">
        <h2 class="h6 mb-3">Default SSH Credential</h2>
        <div class="row g-3">
          <div class="col-md-8">
            <label class="form-label">SSH Credential</label>
            <ssh-credential-selector v-model="resourceSpecificCredentialStoreToken" />
          </div>
        </div>
      </div>
    </div>

    <div class="card mb-3">
      <div class="card-body">
        <h2 class="h6 mb-3">Appearance</h2>
        <p class="text-muted mb-0">Configure in settings_local.py.</p>
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
    };
  },
  methods: {
    async loadSettings() {
      const el = document.getElementById("gateway-settings");
      if (el) {
        this.gateway_id = el.dataset.gateway_id || "";
        this.portalTitle = el.dataset.portalTitle || "";
      }

      try {
        this.storageResources = await services.StorageResourceService.names();
      } catch {
        this.storageResources = {};
      }

      try {
        const profile = await utils.FetchUtils.get("/api/gateway-resource-profile/");
        this.gatewayResourceProfile = profile;
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
  },
  created() {
    this.loadSettings();
  },
};
</script>
