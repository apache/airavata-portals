<template>
  <div>
    <user-storage-create-view
      v-if="includeCreateFileAction && userStoragePath && isDir"
      :user-storage-path="userStoragePath"
      :storage-path="storagePath"
      @upload-finished="$emit('upload-finished')"
      @add-directory="(dirName) => $emit('add-directory', dirName)"
    />
    <user-storage-path-breadcrumb
      v-if="userStoragePath && isDir"
      :parts="userStoragePath.parts"
      @directory-selected="$emit('directory-selected', $event)"
    />

    <user-storage-edit-viewer
      v-if="userStoragePath && isFile"
      :file-name="file.name"
      :data-product-uri="file.data_product_uri"
      :mime-type="file.content_type"
      @file-content-changed="
        (fileContent) => $emit('file-content-changed', fileContent)
      "
    />

    <Table v-if="userStoragePath && isDir">
      <TableHeader>
        <TableRow>
          <TableHead>Name</TableHead>
          <TableHead>Size</TableHead>
          <TableHead>Last Modified</TableHead>
          <TableHead>Actions</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        <TableRow v-for="item in sortedItems" :key="item.path || item.name">
          <TableCell>
            <a
              v-if="item.type === 'dir'"
              href="#"
              class="inline-flex items-center gap-1 text-primary"
              @click.prevent="directorySelected(item)"
            >
              <FolderOpen class="size-4" /> {{ item.name }}
              <template v-if="item.is_shared_dir">
                <Badge variant="secondary" class="ml-1">shared</Badge>
              </template>
            </a>
            <user-storage-link
              v-else
              :data-product-uri="item.data_product_uri"
              :mime-type="item.content_type"
              :file-name="item.name"
              :allow-preview="allowPreview"
            />
          </TableCell>
          <TableCell>{{ getFormattedSize(item.size) }}</TableCell>
          <TableCell>
            <human-date :date="item.modified_time" />
          </TableCell>
          <TableCell>
            <div class="flex flex-wrap items-center gap-2">
              <Button
                v-if="includeSelectFileAction && item.type === 'file'"
                @click="$emit('file-selected', item)"
                :disabled="isAlreadySelected(item)"
                variant="default"
              >
                Select
              </Button>

              <a
                v-if="includeDownloadAction && item.type === 'file'"
                class="inline-flex items-center gap-1 text-primary"
                :href="`${item.downloadURL}&download`"
              >
                Download File
                <Download class="size-4" aria-hidden="true" />
              </a>
              <a
                v-if="includeDownloadAction && item.type === 'dir'"
                class="inline-flex items-center gap-1 text-primary"
                :href="`/sdk/download-dir/?path=${item.path}`"
              >
                Download Zip
                <FileArchive class="size-4" aria-hidden="true" />
              </a>
              <delete-link
                v-if="
                  includeDeleteAction &&
                  item.user_has_write_access &&
                  !item.is_shared_dir
                "
                @delete="deleteItem(item)"
              >
                Are you sure you want to delete
                <strong>{{ item.name }}</strong
                >?
              </delete-link>
            </div>
          </TableCell>
        </TableRow>
      </TableBody>
    </Table>
  </div>
</template>
<script>
import { Download, FileArchive, FolderOpen } from "@lucide/vue";
import UserStoragePathBreadcrumb from "./StoragePathBreadcrumb.vue";
import { components } from "django-airavata-common-ui";
import UserStorageCreateView from "./UserStorageCreateView";
import UserStorageEditViewer from "./storage-edit/UserStorageEditViewer";
import UserStorageLink from "./storage-edit/UserStorageLink";

export default {
  name: "user-storage-path-viewer",
  props: {
    allowPreview: {
      default: true,
      required: false,
    },
    userStoragePath: {
      required: true,
    },
    storagePath: {
      required: true,
    },
    includeDeleteAction: {
      type: Boolean,
      default: true,
    },
    includeSelectFileAction: {
      type: Boolean,
      default: false,
    },
    includeCreateFileAction: {
      type: Boolean,
      default: true,
    },
    includeDownloadAction: {
      type: Boolean,
      default: true,
    },
    downloadInNewWindow: {
      type: Boolean,
      default: false,
    },
    selectedDataProductUris: {
      type: Array,
      default: () => [],
    },
  },
  components: {
    Download,
    FileArchive,
    FolderOpen,
    UserStorageLink,
    "delete-link": components.DeleteLink,
    "human-date": components.HumanDate,
    UserStoragePathBreadcrumb,
    UserStorageCreateView,
    UserStorageEditViewer,
  },
  computed: {
    isDir() {
      return this.userStoragePath.is_dir;
    },
    isFile() {
      return !this.userStoragePath.is_dir;
    },

    // Return the first file available. This is assuming the path is a file.
    file() {
      return this.userStoragePath.files[0];
    },

    items() {
      if (this.userStoragePath) {
        const dirs = this.userStoragePath.directories.map((d) => {
          return {
            name: d.name,
            path: d.path,
            type: "dir",
            modified_time: d.modified_time,
            modifiedTimestamp: d.modified_time.getTime(), // for sorting
            size: d.size,
            user_has_write_access: d.user_has_write_access,
            is_shared_dir: d.is_shared_dir,
          };
        });
        const files = this.userStoragePath.files.map((f) => {
          return {
            name: f.name,
            content_type: f.content_type,
            type: "file",
            data_product_uri: f.data_product_uri,
            // downloadURL is no longer on the wire; build it from the URI.
            downloadURL: `/sdk/download/?data-product-uri=${encodeURIComponent(
              f.data_product_uri,
            )}`,
            modified_time: f.modified_time,
            modifiedTimestamp: f.modified_time.getTime(), // for sorting
            size: f.size,
            user_has_write_access: f.user_has_write_access,
          };
        });
        return dirs.concat(files);
      } else {
        return [];
      }
    },
    sortedItems() {
      // Mirror the b-table sort: shared directories first, then by name.
      return this.items.slice().sort((a, b) => {
        if (a.is_shared_dir && !b.is_shared_dir) {
          return -1;
        }
        if (b.is_shared_dir && !a.is_shared_dir) {
          return 1;
        }
        return a.name.localeCompare(b.name);
      });
    },
    downloadTarget() {
      return this.downloadInNewWindow ? "_blank" : "_self";
    },
    userHasWriteAccess() {
      return this.userStoragePath.user_has_write_access;
    },
  },
  methods: {
    getFormattedSize(size) {
      if (size > Math.pow(2, 30)) {
        return Math.round(size / Math.pow(2, 30)) + " GB";
      } else if (size > Math.pow(2, 20)) {
        return Math.round(size / Math.pow(2, 20)) + " MB";
      } else if (size > Math.pow(2, 10)) {
        return Math.round(size / Math.pow(2, 10)) + " KB";
      } else {
        return size + " bytes";
      }
    },
    deleteItem(item) {
      if (item.type === "dir") {
        this.$emit("delete-dir", item.path);
      } else if (item.type === "file") {
        this.$emit("delete-file", item.data_product_uri);
      }
    },
    directorySelected(item) {
      this.$emit("directory-selected", item.path);
    },
    isAlreadySelected(item) {
      return (
        this.selectedDataProductUris.find(
          (uri) => item.type === "file" && uri === item.data_product_uri,
        ) !== undefined
      );
    },
  },
};
</script>
<style scoped>
.action-link + .delete-link {
  margin-left: 0.25rem;
}
</style>
