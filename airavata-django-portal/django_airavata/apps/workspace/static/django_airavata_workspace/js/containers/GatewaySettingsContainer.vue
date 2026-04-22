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
            <select v-model="storageResourceId" class="form-select form-select-sm">
              <option :value="null">None</option>
              <option v-for="(name, id) in storageResources" :key="id" :value="id">
                {{ name }}
              </option>
            </select>
          </div>
          <div class="col-md-6">
            <label class="form-label">SSH Credential</label>
            <SSHCredentialSelector v-model="resourceSpecificCredentialStoreToken" />
          </div>
          <div class="col-md-6">
            <label class="form-label">Login Username</label>
            <input
              v-model="loginUserName"
              class="form-control form-control-sm"
              placeholder="username"
            />
          </div>
          <div class="col-md-6">
            <label class="form-label">File System Root Location</label>
            <input
              v-model="fileSystemRootLocation"
              class="form-control form-control-sm"
              placeholder="/home/user/storage"
            />
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
            :disabled="localSettingsSaving || localSettingsLoading"
            @click="saveLocalSettings"
          >
            <span v-if="localSettingsSaving"
              ><i class="fa fa-spinner fa-spin me-1"></i>Saving...</span
            >
            <span v-else>Save</span>
          </button>
        </div>
        <p class="text-muted small mb-2">
          Edit <code>django_airavata/settings_local.py</code> directly. Changes take effect after
          the portal restarts. <strong class="text-danger">Warning:</strong> this file executes as
          Python on startup &mdash; mistakes can break the portal.
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
          style="
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
            font-size: 12px;
            white-space: pre;
            tab-size: 4;
          "
        ></textarea>
        <div
          v-if="localSettingsMessage"
          :class="['small', 'mt-2', localSettingsError ? 'text-danger' : 'text-success']"
        >
          {{ localSettingsMessage }}
        </div>
      </div>
    </div>

    <div class="d-flex justify-content-end">
      <button class="btn btn-primary btn-sm" :disabled="saving" @click="saveSettings">
        <span v-if="saving"><i class="fa fa-spinner fa-spin me-1"></i>Saving...</span>
        <span v-else>Save Settings</span>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { services, utils } from "django-airavata-api";
import SSHCredentialSelector from "../../../../../admin/static/django_airavata_admin/src/components/credentials/SSHCredentialSelector.vue";

const saving = ref(false);
const gatewayId = ref("");
const portalTitle = ref("");
const storageResources = ref<Record<string, string>>({});
const gatewayResourceProfile = ref<unknown>(null);
const storageResourceId = ref<string | null>(null);
const fileSystemRootLocation = ref("");
const loginUserName = ref("");
const resourceSpecificCredentialStoreToken = ref<string | null>(null);
const isGatewayAdmin = ref(false);
const localSettingsContent = ref("");
const localSettingsLoading = ref(false);
const localSettingsSaving = ref(false);
const localSettingsMessage = ref("");
const localSettingsError = ref(false);

async function loadSettings() {
  const el = document.getElementById("gateway-settings");
  if (el) {
    gatewayId.value = el.dataset.gatewayId || "";
    portalTitle.value = el.dataset.portalTitle || "";
    isGatewayAdmin.value = el.dataset.isGatewayAdmin === "true";
  }
  if (isGatewayAdmin.value) {
    loadLocalSettings();
  }

  try {
    storageResources.value = await services.StorageResourceService.names() as Record<string, string>;
  } catch {
    storageResources.value = {};
  }

  try {
    const profile = await utils.FetchUtils.get("/api/gateway-resource-profile/");
    gatewayResourceProfile.value = profile;
    const p = profile as Record<string, unknown>;
    if (!gatewayId.value && p?.gateway_id) {
      gatewayId.value = p.gateway_id as string;
    }
    const prefs = p?.storage_preferences as Array<Record<string, unknown>> | undefined;
    const pref = prefs && prefs.length > 0 ? prefs[0] : null;
    if (pref) {
      storageResourceId.value = (pref.storage_resource_id as string) || null;
      fileSystemRootLocation.value = (pref.file_system_root_location as string) || "";
      loginUserName.value = (pref.login_user_name as string) || "";
      resourceSpecificCredentialStoreToken.value =
        (pref.resource_specific_credential_store_token as string) || null;
    }
  } catch {
    gatewayResourceProfile.value = null;
  }
}

async function saveSettings() {
  saving.value = true;
  try {
    const updatedPref = {
      storage_resource_id: storageResourceId.value,
      file_system_root_location: fileSystemRootLocation.value,
      login_user_name: loginUserName.value,
      resource_specific_credential_store_token: resourceSpecificCredentialStoreToken.value,
    };
    const profile = gatewayResourceProfile.value as Record<string, unknown> | null;
    const existingPrefs = profile?.storage_preferences
      ? (profile.storage_preferences as unknown[]).slice(1)
      : [];
    const updatedProfile = Object.assign({}, profile, {
      storage_preferences: [updatedPref, ...existingPrefs],
    });
    await utils.FetchUtils.put("/api/gateway-resource-profile/", updatedProfile);
    gatewayResourceProfile.value = updatedProfile;
  } finally {
    saving.value = false;
  }
}

async function loadLocalSettings() {
  localSettingsLoading.value = true;
  localSettingsMessage.value = "";
  localSettingsError.value = false;
  try {
    const data = await utils.FetchUtils.get("/api/settings/local/") as Record<string, string> | null;
    localSettingsContent.value = data?.content ?? "";
  } catch (e) {
    localSettingsError.value = true;
    localSettingsMessage.value =
      "Failed to load settings_local.py: " + (e instanceof Error ? e.message : String(e));
  } finally {
    localSettingsLoading.value = false;
  }
}

async function saveLocalSettings() {
  localSettingsSaving.value = true;
  localSettingsMessage.value = "";
  localSettingsError.value = false;
  try {
    await utils.FetchUtils.post("/api/settings/local/", {
      content: localSettingsContent.value,
    });
    localSettingsMessage.value = "Saved! Restart the portal for changes to take effect.";
  } catch (e) {
    localSettingsError.value = true;
    localSettingsMessage.value =
      "Failed to save settings_local.py: " + (e instanceof Error ? e.message : String(e));
  } finally {
    localSettingsSaving.value = false;
  }
}

onMounted(() => {
  loadSettings();
});
</script>
