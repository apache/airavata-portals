<template>
  <list-layout
    @add-new-item="addNewStoragePreference"
    :items="decoratedStoragePreferences"
    title="Storage Preferences"
    new-item-button-text="New Storage Preference"
    :new-button-disabled="readonly"
  >
    <template v-slot:new-item-editor>
      <Card v-if="showNewItemEditor">
        <CardHeader>
          <CardTitle>New Storage Preference</CardTitle>
        </CardHeader>
        <CardContent class="space-y-4">
          <div class="space-y-1.5">
            <Label for="storage-resource">Storage Resource</Label>
            <select
              id="storage-resource"
              v-model="newStoragePreference.storage_resource_id"
              class="border-input focus-visible:border-ring focus-visible:ring-ring/50 h-9 w-full rounded-md border bg-transparent px-3 py-1 text-sm shadow-xs outline-none focus-visible:ring-3"
            >
              <option
                v-for="opt in storageResourceOptions"
                :key="opt.value"
                :value="opt.value"
              >
                {{ opt.text }}
              </option>
            </select>
          </div>
          <storage-preference-editor
            v-model="newStoragePreference"
            :default-credential-store-token="defaultCredentialStoreToken"
          />
          <div class="flex gap-2">
            <Button variant="default" @click="saveNewStoragePreference">
              Save
            </Button>
            <Button variant="secondary" @click="cancelNewStoragePreference">
              Cancel
            </Button>
          </div>
        </CardContent>
      </Card>
    </template>
    <template v-slot:item-list="slotProps">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead v-for="field in fields" :key="field.key">
              {{ field.label }}
            </TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          <template
            v-for="item in sortedItems(slotProps.items)"
            :key="item.storage_resource_id"
          >
            <TableRow>
              <TableCell>{{
                getStorageResourceName(item.storage_resource_id)
              }}</TableCell>
              <TableCell>{{ item.login_user_name }}</TableCell>
              <TableCell>
                {{
                  getCredentialName(
                    item.resource_specific_credential_store_token,
                  )
                }}
                <Badge
                  v-if="
                    defaultCredentialStoreToken &&
                    !item.resource_specific_credential_store_token
                  "
                >
                  Default
                </Badge>
              </TableCell>
              <TableCell>{{ item.file_system_root_location }}</TableCell>
              <TableCell>
                <a
                  href="#"
                  v-if="!readonly"
                  class="mr-2 inline-flex items-center gap-1 text-primary hover:underline"
                  @click.prevent="toggleDetails(item)"
                >
                  Edit
                  <Pencil class="size-4" aria-hidden="true" />
                </a>
                <delete-link
                  v-if="!readonly"
                  @delete="deleteStoragePreference(item.storage_resource_id)"
                >
                  Are you sure you want to delete the storage preference for
                  <strong>{{
                    getStorageResourceName(item.storage_resource_id)
                  }}</strong
                  >?
                </delete-link>
              </TableCell>
            </TableRow>
            <TableRow v-if="item._showDetails">
              <TableCell :colspan="fields.length">
                <Card>
                  <CardContent>
                    <storage-preference-editor
                      :model-value="item"
                      @update:model-value="updatedStoragePreference"
                      :default-credential-store-token="
                        defaultCredentialStoreToken
                      "
                    />
                    <Button class="mt-2" size="sm" @click="toggleDetails(item)"
                      >Close</Button
                    >
                  </CardContent>
                </Card>
              </TableCell>
            </TableRow>
          </template>
        </TableBody>
      </Table>
    </template>
  </list-layout>
</template>

<script>
import { Pencil } from "@lucide/vue";
import { models, services, utils } from "django-airavata-api";
import { components, layouts } from "django-airavata-common-ui";
import StoragePreferenceEditor from "./StoragePreferenceEditor.vue";

export default {
  name: "storage-preference-list",
  components: {
    Pencil,
    "delete-link": components.DeleteLink,
    "list-layout": layouts.ListLayout,
    StoragePreferenceEditor,
  },
  props: {
    storagePreferences: {
      type: Array,
      required: true,
    },
    defaultCredentialStoreToken: {
      type: String,
    },
    readonly: {
      type: Boolean,
      default: false,
    },
  },
  data() {
    return {
      showingDetails: {},
      showNewItemEditor: false,
      newStoragePreference: null,
      storageResourceNames: null,
      credentials: null,
    };
  },
  computed: {
    fields() {
      return [
        {
          label: "Name",
          key: "storage_resource_id",
          sortable: true,
          formatter: (value) => this.getStorageResourceName(value),
        },
        {
          label: "Username",
          key: "login_user_name",
        },
        {
          label: "SSH Credential",
          key: "resource_specific_credential_store_token",
          formatter: (value) => this.getCredentialName(value),
        },
        {
          label: "File System Location",
          key: "file_system_root_location",
        },
        {
          label: "Action",
          key: "action",
        },
      ];
    },
    decoratedStoragePreferences() {
      return this.storagePreferences.map((sp) => {
        const spClone = sp.clone();
        spClone._showDetails = this.showingDetails[spClone.storage_resource_id];
        return spClone;
      });
    },
    currentStoragePreferenceIds() {
      return this.storagePreferences.map((sp) => sp.storage_resource_id);
    },
    storageResourceOptions() {
      const options = [];
      for (const key in this.storageResourceNames) {
        if (
          Object.prototype.hasOwnProperty.call(
            this.storageResourceNames,
            key,
          ) &&
          this.currentStoragePreferenceIds.indexOf(key) < 0
        ) {
          const name = this.storageResourceNames[key];
          options.push({
            value: key,
            text: name,
          });
        }
      }
      return utils.StringUtils.sortIgnoreCase(options, (a) => a.text);
    },
    defaultCredentialSummary() {
      if (this.defaultCredentialStoreToken && this.credentials) {
        return this.credentials.find(
          (cred) => cred.token === this.defaultCredentialStoreToken,
        );
      } else {
        return null;
      }
    },
  },
  created() {
    services.StorageResourceService.names().then((names) => {
      this.storageResourceNames = names;
    });
    services.CredentialSummaryService.allSSHCredentials().then(
      (creds) => (this.credentials = creds),
    );
  },
  methods: {
    getStorageResourceName(storageResourceId) {
      if (
        this.storageResourceNames &&
        storageResourceId in this.storageResourceNames
      ) {
        return this.storageResourceNames[storageResourceId];
      } else {
        return storageResourceId.substring(0, 10) + "...";
      }
    },
    getCredentialName(token) {
      if (token === null && this.defaultCredentialSummary) {
        return this.defaultCredentialSummary.description;
      } else if (this.credentials) {
        const cred = this.credentials.find((cred) => cred.token === token);
        if (cred) {
          return cred.description;
        }
      }
      return "...";
    },
    updatedStoragePreference(newValue) {
      this.$emit("updated", newValue);
    },
    sortedItems(items) {
      return utils.StringUtils.sortIgnoreCase(items.slice(), (sp) =>
        this.getStorageResourceName(sp.storage_resource_id),
      );
    },
    toggleDetails(item) {
      this.showingDetails[item.storage_resource_id] =
        !this.showingDetails[item.storage_resource_id];
    },
    deleteStoragePreference(storageResourceId) {
      this.$emit("delete", storageResourceId);
    },
    addNewStoragePreference() {
      this.newStoragePreference = new models.StoragePreference();
      this.showNewItemEditor = true;
    },
    saveNewStoragePreference() {
      this.$emit("added", this.newStoragePreference);
      this.showNewItemEditor = false;
    },
    cancelNewStoragePreference() {
      this.showNewItemEditor = false;
    },
  },
};
</script>
