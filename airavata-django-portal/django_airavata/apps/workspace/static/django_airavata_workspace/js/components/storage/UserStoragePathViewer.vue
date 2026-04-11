<template>
  <div>
    <user-storage-edit-viewer
      v-if="userStoragePath && isFile"
      :file-name="file.name"
      :data-product-uri="file.data_product_uri"
      :mime-type="file.mime_type"
      @file-content-changed="(fileContent) => $emit('file-content-changed', fileContent)"
    />

    <div v-if="userStoragePath && isDir" class="card">
      <div class="card-body">
        <!-- Toolbar: breadcrumb + upload/add controls -->
        <div class="d-flex align-items-center justify-content-between mb-2">
          <nav aria-label="breadcrumb" class="mb-0">
            <ol class="breadcrumb mb-0" style="font-size:0.8125rem;">
              <li class="breadcrumb-item"
                v-for="item in breadcrumbItems" :key="item.path"
                :class="{ active: item.active }"
                @click="!item.active && $emit('directory-selected', item.path)"
                :style="item.active ? '' : 'cursor:pointer;'"
              >
                <i v-if="item.isHome" class="fa fa-home me-1"></i>{{ item.text }}
              </li>
            </ol>
          </nav>
          <user-storage-create-view
            v-if="includeCreateFileAction"
            :user-storage-path="userStoragePath"
            :storage-path="storagePath"
            @upload-finished="$emit('upload-finished')"
            @add-directory="(dirName) => $emit('add-directory', dirName)"
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
                  <div class="table-empty__text">Upload files or create a subdirectory using the controls above.</div>
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
                  <user-storage-link
                    :data-product-uri="item.data_product_uri"
                    :mime-type="item.mime_type"
                    :file-name="item.name"
                    :allow-preview="allowPreview"
                  />
                </span>
              </td>
              <td>{{ getFormattedSize(item.size) }}</td>
              <td><human-date :date="item.modified_time" /></td>
              <td>
                <button class="btn btn-primary btn-sm me-1" v-if="includeSelectFileAction && item.type === 'file'"
                  @click="$emit('file-selected', item)" :disabled="isAlreadySelected(item)">Select</button>
                <a v-if="includeDownloadAction && item.type === 'file'" class="action-link me-2"
                  :href="`${item.download_url}&download`"><i class="fa fa-download"></i> Download</a>
                <a v-if="includeDownloadAction && item.type === 'dir'" class="action-link me-2"
                  :href="`/sdk/download-dir/?path=${item.path}`"><i class="fa fa-file-archive"></i> Zip</a>
                <delete-link v-if="includeDeleteAction && item.user_has_write_access && !item.is_shared_dir"
                  @delete="deleteItem(item)">
                  Are you sure you want to delete <strong>{{ item.name }}</strong>?
                </delete-link>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
<script>
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

    breadcrumbItems() {
      const parts = this.userStoragePath.parts || [];
      const subparts = [];
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
        const dirs = this.userStoragePath.directories
          .filter((d) => !d.hidden)
          .map((d) => {
            return {
              name: d.name,
              path: d.path,
              type: "dir",
              modifiedTime: d.modified_time,
              modifiedTimestamp: d.modified_time ? d.modified_time.getTime() : 0,
              size: d.size,
              userHasWriteAccess: d.user_has_write_access,
              isSharedDir: d.is_shared_dir,
            };
          });
        const files = this.userStoragePath.files.map((f) => {
          return {
            name: f.name,
            mimeType: f.mime_type,
            type: "file",
            dataProductURI: f.data_product_uri,
            downloadURL: f.download_url,
            modifiedTime: f.modified_time,
            modifiedTimestamp: f.modified_time ? f.modified_time.getTime() : 0,
            size: f.size,
            userHasWriteAccess: f.user_has_write_access,
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
