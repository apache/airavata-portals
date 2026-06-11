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

    <b-table
      v-if="userStoragePath && isDir"
      :fields="fields"
      :items="items"
      sort-by="name"
      :sort-compare="sortCompare"
    >
      <template slot="cell(name)" slot-scope="data">
        <b-link
          v-if="data.item.type === 'dir'"
          @click="directorySelected(data.item)"
        >
          <i class="fa fa-folder-open"></i> {{ data.item.name }}
          <template v-if="data.item.is_shared_dir">
            <b-badge class="ml-1">shared</b-badge>
          </template>
        </b-link>
        <user-storage-link
          v-else
          :data-product-uri="data.item.data_product_uri"
          :mime-type="data.item.content_type"
          :file-name="data.item.name"
          :allow-preview="allowPreview"
        />
      </template>
      <template slot="cell(modifiedTimestamp)" slot-scope="data">
        <human-date :date="data.item.modified_time" />
      </template>
      <template slot="cell(actions)" slot-scope="data">
        <b-button
          v-if="includeSelectFileAction && data.item.type === 'file'"
          @click="$emit('file-selected', data.item)"
          :disabled="isAlreadySelected(data.item)"
          variant="primary"
        >
          Select
        </b-button>

        <b-link
          v-if="includeDownloadAction && data.item.type === 'file'"
          class="action-link"
          :href="`${data.item.downloadURL}&download`"
        >
          Download File
          <i class="fa fa-download" aria-hidden="true"></i>
        </b-link>
        <b-link
          v-if="includeDownloadAction && data.item.type === 'dir'"
          class="action-link"
          :href="`/sdk/download-dir/?path=${data.item.path}`"
        >
          Download Zip
          <i class="fa fa-file-archive" aria-hidden="true"></i>
        </b-link>
        <delete-link
          v-if="
            includeDeleteAction &&
            data.item.user_has_write_access &&
            !data.item.is_shared_dir
          "
          @delete="deleteItem(data.item)"
        >
          Are you sure you want to delete <strong>{{ data.item.name }}</strong
          >?
        </delete-link>
      </template>
    </b-table>
  </div>
</template>
<script>
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

    fields() {
      return [
        {
          label: "Name",
          key: "name",
          sortable: true,
        },
        {
          label: "Size",
          key: "size",
          sortable: true,
          formatter: (value) => this.getFormattedSize(value),
        },
        {
          label: "Last Modified",
          key: "modifiedTimestamp",
          sortable: true,
        },
        {
          label: "Actions",
          key: "actions",
        },
      ];
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
              f.data_product_uri
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
          (uri) => item.type === "file" && uri === item.data_product_uri
        ) !== undefined
      );
    },
    sortCompare(aRow, bRow, key) {
      if (key === "name") {
        // Sort the shared directory first
        if (aRow.is_shared_dir) {
          return -1;
        }
        if (bRow.is_shared_dir) {
          return 1;
        }
        const a = aRow[key];
        const b = bRow[key];
        return a.localeCompare(b);
      } else {
        // Use default logic for all other fields
        return null;
      }
    },
  },
};
</script>
<style scoped>
.action-link + .delete-link {
  margin-left: 0.25rem;
}
</style>
