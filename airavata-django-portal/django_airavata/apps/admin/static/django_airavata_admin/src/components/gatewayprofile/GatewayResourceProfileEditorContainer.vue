<template>
  <div>
    <div class="row">
      <div class="col">
        <div class="card">
          <div class="card-body">
            <gateway-resource-profile-editor
              v-if="gatewayResourceProfile"
              v-model="gatewayResourceProfile"
            />
          </div>
        </div>
      </div>
    </div>
    <div class="row">
      <div class="col">
        <div class="card">
          <div class="card-body">
            <storage-preference-list
              v-if="gatewayResourceProfile"
              :storage-preferences="gatewayResourceProfile.storage_preferences"
              :default-credential-store-token="gatewayResourceProfile.credential_store_token"
              :readonly="!gatewayResourceProfile.user_has_write_access"
              @updated="updatedStoragePreference"
              @added="addedStoragePreference"
              @delete="deleteStoragePreference"
            />
          </div>
        </div>
      </div>
    </div>
    <div v-if="gatewayResourceProfile && gatewayResourceProfile.user_has_write_access" class="row">
      <div class="col">
        <button class="btn btn-primary btn-sm" @click="save">Save</button>
        <button class="btn btn-secondary btn-sm" @click="cancel">Cancel</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { services } from "django-airavata-api";
import GatewayResourceProfileEditor from "./GatewayResourceProfileEditor.vue";
import StoragePreferenceList from "./StoragePreferenceList.vue";

interface StoragePreference {
  storage_resource_id: string;
  login_user_name?: string;
  resource_specific_credential_store_token?: string | null;
  file_system_root_location?: string;
  clone?(): StoragePreference;
}

interface GatewayResourceProfile {
  gateway_id: string;
  credential_store_token?: string;
  user_has_write_access?: boolean;
  storage_preferences: StoragePreference[];
  clone(): GatewayResourceProfile;
}

const gatewayResourceProfile = ref<GatewayResourceProfile | null>(null);
const gatewayResourceProfileClone = ref<GatewayResourceProfile | null>(null);

onMounted(() => {
  services.GatewayResourceProfileService.get().then((gwp: GatewayResourceProfile) => {
    gatewayResourceProfile.value = gwp;
    gatewayResourceProfileClone.value = gwp.clone();
  });
});

function save() {
  services.GatewayResourceProfileService.update({
    data: gatewayResourceProfile.value,
  }).then((gwp: GatewayResourceProfile) => {
    gatewayResourceProfile.value = gwp;
    gatewayResourceProfileClone.value = gwp.clone();
  });
}

function cancel() {
  if (gatewayResourceProfileClone.value) {
    gatewayResourceProfile.value = gatewayResourceProfileClone.value.clone();
  }
}

function updatedStoragePreference(updatedSp: StoragePreference) {
  const prefs = gatewayResourceProfile.value?.storage_preferences ?? [];
  const index = prefs.findIndex(
    (sp) => sp.storage_resource_id === updatedSp.storage_resource_id,
  );
  prefs.splice(index, 1, updatedSp);
}

function addedStoragePreference(newSp: StoragePreference) {
  services.StoragePreferenceService.create({
    data: newSp,
  }).then((sp: StoragePreference) => {
    gatewayResourceProfile.value?.storage_preferences.push(sp);
  });
}

function deleteStoragePreference(storageResourceId: string) {
  services.StoragePreferenceService.delete({
    lookup: storageResourceId,
  }).then(() => {
    const prefs = gatewayResourceProfile.value?.storage_preferences ?? [];
    const index = prefs.findIndex((sp) => sp.storage_resource_id === storageResourceId);
    prefs.splice(index, 1);
  });
}
</script>
