<template>
  <main-layout
    title="Gateway Resource Profile"
    subtitle="Configure gateway-wide storage and resource preferences."
  >
    <template
      v-slot:actions
      v-if="
        gatewayResourceProfile && gatewayResourceProfile.user_has_write_access
      "
    >
      <Button variant="secondary" @click="cancel"> Cancel </Button>
      <Button @click="save"> Save </Button>
    </template>
    <div class="space-y-4">
      <Card>
        <CardContent>
          <gateway-resource-profile-editor
            v-if="gatewayResourceProfile"
            v-model="gatewayResourceProfile"
          />
        </CardContent>
      </Card>
      <Card>
        <CardContent>
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
        </CardContent>
      </Card>
    </div>
  </main-layout>
</template>

<script>
import { services } from "django-airavata-api";
import { components } from "django-airavata-common-ui";
import GatewayResourceProfileEditor from "./GatewayResourceProfileEditor.vue";
import StoragePreferenceList from "./StoragePreferenceList.vue";

export default {
  name: "gateway-resource-profile-editor-container",
  components: {
    "main-layout": components.MainLayout,
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
          sp.storage_resource_id ===
          updatedStoragePreference.storage_resource_id,
      );
      this.gatewayResourceProfile.storage_preferences.splice(
        index,
        1,
        updatedStoragePreference,
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
          (sp) => sp.storage_resource_id === storageResourceId,
        );
        this.gatewayResourceProfile.storage_preferences.splice(index, 1);
      });
    },
  },
};
</script>
