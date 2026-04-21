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

<script>
import { services } from "django-airavata-api";
import GatewayResourceProfileEditor from "./GatewayResourceProfileEditor.vue";
import StoragePreferenceList from "./StoragePreferenceList.vue";

export default {
  name: "GatewayResourceProfileEditorContainer",
  components: {
    GatewayResourceProfileEditor,
    StoragePreferenceList,
  },
  data() {
    return {
      gatewayResourceProfile: null,
      gatewayResourceProfileClone: null,
    };
  },
  created() {
    services.GatewayResourceProfileService.get().then((gwp) => {
      this.gatewayResourceProfile = gwp;
      this.gatewayResourceProfileClone = gwp.clone();
    });
  },
  methods: {
    save() {
      services.GatewayResourceProfileService.update({
        data: this.gatewayResourceProfile,
      }).then((gwp) => {
        this.gatewayResourceProfile = gwp;
        this.gatewayResourceProfileClone = gwp.clone();
      });
    },
    cancel() {
      this.gatewayResourceProfile = this.gatewayResourceProfileClone.clone();
    },
    updatedStoragePreference(updatedStoragePreference) {
      const index = this.gatewayResourceProfile.storage_preferences.findIndex(
        (sp) => sp.storage_resource_id === updatedStoragePreference.storage_resource_id,
      );
      this.gatewayResourceProfile.storage_preferences.splice(index, 1, updatedStoragePreference);
    },
    addedStoragePreference(newStoragePreference) {
      services.StoragePreferenceService.create({
        data: newStoragePreference,
      }).then((sp) => {
        this.gatewayResourceProfile.storage_preferences.push(sp);
      });
    },
    deleteStoragePreference(storageResourceId) {
      services.StoragePreferenceService.delete({
        lookup: storageResourceId,
      }).then(() => {
        const index = this.gatewayResourceProfile.storage_preferences.findIndex(
          (sp) => sp.storage_resource_id === storageResourceId,
        );
        this.gatewayResourceProfile.storage_preferences.splice(index, 1);
      });
    },
  },
};
</script>
