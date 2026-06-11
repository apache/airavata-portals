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
              :storagePreferences="gatewayResourceProfile.storage_preferences"
              :default-credential-store-token="
                gatewayResourceProfile.credential_store_token
              "
              @updated="updatedStoragePreference"
              @added="addedStoragePreference"
              @delete="deleteStoragePreference"
              :readonly="!gatewayResourceProfile.user_has_write_access"
            />
          </div>
        </div>
      </div>
    </div>
    <div
      class="row"
      v-if="gatewayResourceProfile && gatewayResourceProfile.user_has_write_access"
    >
      <div class="col">
        <b-button variant="primary" @click="save"> Save </b-button>
        <b-button variant="secondary" @click="cancel"> Cancel </b-button>
      </div>
    </div>
  </div>
</template>

<script>
import { services } from "django-airavata-api";
import GatewayResourceProfileEditor from "./GatewayResourceProfileEditor.vue";
import StoragePreferenceList from "./StoragePreferenceList.vue";

export default {
  name: "gateway-resource-profile-editor-container",
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
        (sp) =>
          sp.storage_resource_id === updatedStoragePreference.storage_resource_id
      );
      this.gatewayResourceProfile.storage_preferences.splice(
        index,
        1,
        updatedStoragePreference
      );
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
          (sp) => sp.storage_resource_id === storageResourceId
        );
        this.gatewayResourceProfile.storage_preferences.splice(index, 1);
      });
    },
  },
};
</script>
