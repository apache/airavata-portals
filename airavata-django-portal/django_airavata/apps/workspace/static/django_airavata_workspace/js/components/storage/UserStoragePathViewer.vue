<template>
  <div>
    <UserStorageEditViewer
      v-if="userStoragePath && isFile"
      :file-name="file.name"
      :data-product-uri="file.data_product_uri"
      :mime-type="file.mime_type"
      @file-content-changed="(fileContent) => emit('file-content-changed', fileContent)"
    />

    <div v-if="userStoragePath && isDir" class="card">
      <div class="card-body">
        <!-- Toolbar: breadcrumb + upload/add controls -->
        <div class="d-flex align-items-center justify-content-between mb-2">
          <nav aria-label="breadcrumb" class="mb-0">
            <ol class="breadcrumb mb-0" style="font-size: 0.8125rem">
              <li
                v-for="item in breadcrumbItems"
                :key="item.path"
                class="breadcrumb-item"
                :class="{ active: item.active }"
                :style="item.active ? '' : 'cursor:pointer;'"
                @click="!item.active && emit('directory-selected', item.path)"
              >
                <i v-if="item.isHome" class="fa fa-home me-1"></i>{{ item.text }}
              </li>
            </ol>
          </nav>
          <UserStorageCreateView
            v-if="includeCreateFileAction"
            :user-storage-path="userStoragePath"
            :storage-path="storagePath"
            @upload-finished="emit('upload-finished')"
            @add-directory="(dirName) => emit('add-directory', dirName)"
          />
        </div>

        <!-- Files table -->
        <table class="table table-hover">
          <thead>
            <tr>
              <th>Name</th>
              <th>Size</th>
              <th>Last Modified</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="items.length === 0">
              <td colspan="4">
                <div class="table-empty">
                  <i class="fa fa-hdd table-empty__icon"></i>
                  <div class="table-empty__title">This directory is empty</div>
                  <div class="table-empty__text">
                    Upload files or create a subdirectory using the controls above.
                  </div>
                </div>
              </td>
            </tr>
            <tr v-for="item in items" :key="item.name">
              <td>
                <a v-if="item.type === 'dir'" href="#" @click.prevent="directorySelected(item)">
                  <i class="fa fa-folder me-1 text-warning"></i>{{ item.name }}
                  <span v-if="item.is_shared_dir" class="badge bg-secondary ms-1">shared</span>
                </a>
                <span v-else>
                  <i class="fa fa-file me-1 text-muted"></i>
                  <UserStorageLink
                    :data-product-uri="item.data_product_uri"
                    :mime-type="item.mime_type"
                    :file-name="item.name"
                    :allow-preview="allowPreview"
                  />
                </span>
              </td>
              <td>{{ getFormattedSize(item.size) }}</td>
              <td><HumanDate :date="item.modified_time" /></td>
              <td>
                <button
                  v-if="includeSelectFileAction && item.type === 'file'"
                  class="btn btn-primary btn-sm me-1"
                  :disabled="isAlreadySelected(item)"
                  @click="emit('file-selected', item)"
                >
                  Select
                </button>
                <a
                  v-if="includeDownloadAction && item.type === 'file'"
                  class="action-link me-2"
                  :href="`${item.download_url}&download`"
                  ><i class="fa fa-download"></i> Download</a
                >
                <a
                  v-if="includeDownloadAction && item.type === 'dir'"
                  class="action-link me-2"
                  :href="`/sdk/download-dir/?path=${item.path}`"
                  ><i class="fa fa-file-archive"></i> Zip</a
                >
                <DeleteLink
                  v-if="includeDeleteAction && item.user_has_write_access && !item.is_shared_dir"
                  @delete="deleteItem(item)"
                >
                  Are you sure you want to delete <strong>{{ item.name }}</strong
                  >?
                </DeleteLink>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { components } from "django-airavata-common-ui";
import UserStorageCreateView from "./UserStorageCreateView.vue";
import UserStorageEditViewer from "./storage-edit/UserStorageEditViewer.vue";
import UserStorageLink from "./storage-edit/UserStorageLink.vue";

const DeleteLink = components.DeleteLink;
const HumanDate = components.HumanDate;

interface StorageDirectory {
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
  directories: StorageDirectory[];
  files: StorageFile[];
  user_has_write_access: boolean;
}

interface DirItem {
  name: string;
  path: string;
  type: "dir";
  modified_time?: Date;
  size: number;
  user_has_write_access: boolean;
  is_shared_dir?: boolean;
  data_product_uri: string;
  mime_type: string;
  download_url?: string;
}

interface FileItem {
  name: string;
  mime_type: string;
  type: "file";
  data_product_uri: string;
  download_url?: string;
  modified_time?: Date;
  size: number;
  user_has_write_access: boolean;
  is_shared_dir: boolean;
  path: string;
}

type StorageItem = DirItem | FileItem;

interface BreadcrumbItem {
  text: string;
  path: string;
  active: boolean;
  isHome: boolean;
}

const props = withDefaults(
  defineProps<{
    allowPreview?: boolean;
    userStoragePath: UserStoragePathData;
    storagePath: string;
    includeDeleteAction?: boolean;
    includeSelectFileAction?: boolean;
    includeCreateFileAction?: boolean;
    includeDownloadAction?: boolean;
    downloadInNewWindow?: boolean;
    selectedDataProductUris?: string[];
  }>(),
  {
    allowPreview: true,
    includeDeleteAction: true,
    includeSelectFileAction: false,
    includeCreateFileAction: true,
    includeDownloadAction: true,
    downloadInNewWindow: false,
    selectedDataProductUris: () => [],
  },
);

const emit = defineEmits<{
  "file-selected": [item: StorageItem];
  "directory-selected": [path: string];
  "delete-dir": [path: string];
  "delete-file": [dataProductUri: string];
  "upload-finished": [];
  "add-directory": [dirName: string];
  "file-content-changed": [fileContent: string];
}>();

const isDir = computed(() => props.userStoragePath.is_dir);
const isFile = computed(() => !props.userStoragePath.is_dir);

const file = computed(() => props.userStoragePath.files[0] as StorageFile);

const breadcrumbItems = computed<BreadcrumbItem[]>(() => {
  const parts = props.userStoragePath.parts ?? [];
  const subparts: string[] = [];
  const items = parts.map((part, index) => {
    subparts.push(part);
    return {
      text: part,
      path: subparts.join("/"),
      active: index === parts.length - 1,
      isHome: false,
    };
  });
  return [{ text: "Home", path: "", active: parts.length === 0, isHome: true }].concat(items);
});

const items = computed<StorageItem[]>(() => {
  if (props.userStoragePath) {
    const dirs: DirItem[] = props.userStoragePath.directories
      .filter((d) => !d.hidden)
      .map((d) => ({
        name: d.name,
        path: d.path,
        type: "dir" as const,
        modified_time: d.modified_time,
        size: d.size,
        user_has_write_access: d.user_has_write_access,
        is_shared_dir: d.is_shared_dir,
        data_product_uri: "",
        mime_type: "",
      }));
    const files: FileItem[] = props.userStoragePath.files.map((f) => ({
      name: f.name,
      mime_type: f.mime_type,
      type: "file" as const,
      data_product_uri: f.data_product_uri,
      download_url: f.download_url,
      modified_time: f.modified_time,
      size: f.size,
      user_has_write_access: f.user_has_write_access,
      is_shared_dir: false,
      path: "",
    }));
    return (dirs as StorageItem[]).concat(files as StorageItem[]);
  } else {
    return [];
  }
});

function getFormattedSize(size: number) {
  if (size > Math.pow(2, 30)) {
    return Math.round(size / Math.pow(2, 30)) + " GB";
  } else if (size > Math.pow(2, 20)) {
    return Math.round(size / Math.pow(2, 20)) + " MB";
  } else if (size > Math.pow(2, 10)) {
    return Math.round(size / Math.pow(2, 10)) + " KB";
  } else {
    return size + " bytes";
  }
}

function deleteItem(item: StorageItem) {
  if (item.type === "dir") {
    emit("delete-dir", item.path);
  } else if (item.type === "file") {
    emit("delete-file", item.data_product_uri);
  }
}

function directorySelected(item: StorageItem) {
  emit("directory-selected", item.path ?? "");
}

function isAlreadySelected(item: StorageItem) {
  return (
    props.selectedDataProductUris.find(
      (uri) => item.type === "file" && uri === item.data_product_uri,
    ) !== undefined
  );
}
</script>

<style scoped>
.action-link + .delete-link {
  margin-left: 0.25rem;
}
</style>
