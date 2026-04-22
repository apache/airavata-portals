<template>
  <div class="card">
    <div class="card-header">Select a file</div>
    <div class="card-body">
      <UserStoragePathViewer
        v-if="userStoragePath"
        :user-storage-path="userStoragePath"
        :storage-path="storagePath"
        :include-delete-action="false"
        :include-select-file-action="true"
        :include-create-file-action="false"
        :include-download-action="false"
        :download-in-new-window="true"
        :selected-data-product-uris="selectedDataProductUris"
        @directory-selected="directorySelected"
        @file-selected="fileSelected"
      />
    </div>
    <div class="card-footer d-flex justify-content-end">
      <a class="text-secondary" @click="emit('cancel')">Cancel</a>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from "vue";
import { services } from "django-airavata-api";
import UserStoragePathViewer from "./UserStoragePathViewer.vue";

// Keep track of most recent path so that when user needs to select an
// additional file they are taken back to the last path
let mostRecentPath = "~";

interface StorageDir {
  name: string;
  path: string;
  hidden?: boolean;
  modified_time?: Date;
  size: number;
  user_has_write_access: boolean;
  is_shared_dir?: boolean;
}

interface StorageFile {
  name: string;
  mime_type: string;
  data_product_uri: string;
  download_url?: string;
  modified_time?: Date;
  size: number;
  user_has_write_access: boolean;
}

interface UserStoragePathData {
  is_dir: boolean;
  parts?: string[];
  directories: StorageDir[];
  files: StorageFile[];
  user_has_write_access: boolean;
}

interface StorageItem {
  type: "file" | "dir";
  data_product_uri: string;
  name: string;
  path?: string;
  mime_type?: string;
  download_url?: string;
  size: number;
  modified_time?: Date;
  user_has_write_access: boolean;
  is_shared_dir?: boolean;
}

withDefaults(
  defineProps<{
    selectedDataProductUris?: string[];
  }>(),
  { selectedDataProductUris: () => [] },
);

const emit = defineEmits<{
  "file-selected": [dataProductUri: string];
  cancel: [];
}>();

const userStoragePath = ref<UserStoragePathData | null>(null);

const storagePath = computed(() => {
  if (!userStoragePath.value) return "~/";
  const parts = userStoragePath.value.parts ?? [];
  return ["~"].concat(parts).join("/") + "/";
});

function loadUserStoragePath(path: string) {
  return services.UserStoragePathService.get({
    path,
  }).then((result: unknown) => {
    userStoragePath.value = result as UserStoragePathData;
  });
}

function directorySelected(path: string) {
  mostRecentPath = "~/" + path;
  return loadUserStoragePath(mostRecentPath);
}

function fileSelected(item: StorageItem) {
  emit("file-selected", item.data_product_uri);
}

// created
loadUserStoragePath(mostRecentPath);
</script>
