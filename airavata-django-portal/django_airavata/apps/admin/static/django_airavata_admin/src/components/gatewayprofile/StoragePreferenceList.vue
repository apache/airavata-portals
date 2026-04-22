<template>
  <list-layout
    :items="decoratedStoragePreferences"
    title="Storage Preferences"
    new-item-button-text="New Storage Preference"
    :new-button-disabled="readonly"
    @add-new-item="addNewStoragePreference"
  >
    <template #new-item-editor>
      <div v-if="showNewItemEditor" class="card" title="New Storage Preference">
        <div class="mb-3" label="Storage Resource" label-for="storage-resource">
          <select
            id="storage-resource"
            v-model="newStoragePreference.storage_resource_id"
            class="form-select"
            :options="storageResourceOptions"
          />
        </div>
        <storage-preference-editor
          v-model="newStoragePreference"
          :default-credential-store-token="defaultCredentialStoreToken"
        />
        <div class="row">
          <div class="col">
            <button class="btn btn-primary btn-sm" @click="saveNewStoragePreference">Save</button>
            <button class="btn btn-secondary btn-sm" @click="cancelNewStoragePreference">
              Cancel
            </button>
          </div>
        </div>
      </div>
    </template>
    <template #item-list="slotProps">
      <table class="table table-hover">
        <thead>
          <tr>
            <th>Name</th>
            <th>Username</th>
            <th>SSH Credential</th>
            <th>File System Location</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in slotProps.items" :key="item.storage_resource_id">
            <td>{{ getStorageResourceName(item.storage_resource_id) }}</td>
            <td>{{ item.login_user_name }}</td>
            <td>
              {{ getCredentialName(item.resource_specific_credential_store_token) }}
              <span
                v-if="defaultCredentialStoreToken && !item.resource_specific_credential_store_token"
                class="badge"
              >
                Default
              </span>
            </td>
            <td>{{ item.file_system_root_location }}</td>
            <td>
              <a v-if="!readonly" class="action-link" @click="toggleDetails(item)">
                Edit
                <i class="fa fa-edit" aria-hidden="true"></i>
              </a>
              <delete-link
                v-if="!readonly"
                class="action-link"
                @delete="deleteStoragePreference(item.storage_resource_id)"
              >
                Are you sure you want to delete the storage preference for
                <strong>{{ getStorageResourceName(item.storage_resource_id) }}</strong>?
              </delete-link>
            </td>
          </tr>
          <tr v-for="item in slotProps.items.filter((i: StoragePreference) => showingDetails[i.storage_resource_id])" :key="item.storage_resource_id + '-detail'">
            <td colspan="5">
              <div class="card">
                <div class="card-body">
                  <storage-preference-editor
                    :model-value="item"
                    :default-credential-store-token="defaultCredentialStoreToken"
                    @update:model-value="updatedStoragePreference"
                  />
                  <button class="btn btn-sm" @click="toggleDetails(item)">Close</button>
                </div>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </template>
  </list-layout>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { models, services, utils } from "django-airavata-api";
import { components, layouts } from "django-airavata-common-ui";
import StoragePreferenceEditor from "./StoragePreferenceEditor.vue";

const ListLayout = layouts.ListLayout;
const DeleteLink = components.DeleteLink;

interface StoragePreference {
  storage_resource_id: string;
  login_user_name?: string;
  resource_specific_credential_store_token?: string | null;
  file_system_root_location?: string;
  clone?(): StoragePreference;
}

interface CredentialSummary {
  token: string;
  description?: string;
}

const props = defineProps<{
  storagePreferences: StoragePreference[];
  defaultCredentialStoreToken?: string;
  readonly?: boolean;
}>();

const emit = defineEmits<{
  updated: [sp: StoragePreference];
  added: [sp: StoragePreference];
  delete: [storageResourceId: string];
}>();

const showingDetails = ref<Record<string, boolean>>({});
const showNewItemEditor = ref(false);
const newStoragePreference = ref<Record<string, unknown>>({});
const storageResourceNames = ref<Record<string, string> | null>(null);
const credentials = ref<CredentialSummary[] | null>(null);

const decoratedStoragePreferences = computed(() =>
  props.storagePreferences.map((sp) => {
    const spClone = sp.clone ? sp.clone() : { ...sp };
    return spClone;
  }),
);

const currentStoragePreferenceIds = computed(() =>
  props.storagePreferences.map((sp) => sp.storage_resource_id),
);

const storageResourceOptions = computed(() => {
  const options: Array<{ value: string; text: string }> = [];
  for (const key in storageResourceNames.value) {
    if (
      Object.prototype.hasOwnProperty.call(storageResourceNames.value, key) &&
      currentStoragePreferenceIds.value.indexOf(key) < 0
    ) {
      options.push({ value: key, text: storageResourceNames.value[key] });
    }
  }
  return utils.StringUtils.sortIgnoreCase(options, (a: { text: string }) => a.text);
});

const defaultCredentialSummary = computed(() => {
  if (props.defaultCredentialStoreToken && credentials.value) {
    return credentials.value.find(
      (cred) => cred.token === props.defaultCredentialStoreToken,
    );
  } else {
    return null;
  }
});

onMounted(() => {
  services.StorageResourceService.names().then(
    (names: Record<string, string>) => (storageResourceNames.value = names),
  );
  services.CredentialSummaryService.allSSHCredentials().then(
    (creds: CredentialSummary[]) => (credentials.value = creds),
  );
});

function getStorageResourceName(storageResourceId: string) {
  if (storageResourceNames.value && storageResourceId in storageResourceNames.value) {
    return storageResourceNames.value[storageResourceId];
  } else {
    return storageResourceId.substring(0, 10) + "...";
  }
}

function getCredentialName(token: string | null | undefined) {
  if (token === null && defaultCredentialSummary.value) {
    return defaultCredentialSummary.value.description;
  } else if (credentials.value) {
    const cred = credentials.value.find((c) => c.token === token);
    if (cred) {
      return cred.description;
    }
  }
  return "...";
}

function updatedStoragePreference(newValue: Record<string, unknown>) {
  emit("updated", newValue as unknown as StoragePreference);
}

function toggleDetails(item: StoragePreference) {
  showingDetails.value[item.storage_resource_id] = !showingDetails.value[item.storage_resource_id];
}

function deleteStoragePreference(storageResourceId: string) {
  emit("delete", storageResourceId);
}

function addNewStoragePreference() {
  newStoragePreference.value = new models.StoragePreference() as unknown as Record<string, unknown>;
  showNewItemEditor.value = true;
}

function saveNewStoragePreference() {
  emit("added", newStoragePreference.value as unknown as StoragePreference);
  showNewItemEditor.value = false;
}

function cancelNewStoragePreference() {
  showNewItemEditor.value = false;
}
</script>
