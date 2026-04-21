<template>
  <div class="card">
    <div class="card-header">Select a file</div>
    <div class="card-body">
      <user-storage-path-viewer
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
      <a class="text-secondary" @click="$emit('cancel')">Cancel</a>
    </div>
  </div>
</template>

<script>
import { services } from "django-airavata-api";
import UserStoragePathViewer from "./UserStoragePathViewer";

// Keep track of most recent path so that when user needs to select an
// additional file they are taken back to the last path
let mostRecentPath = "~";

export default {
  name: "UserStorageFileSelectionContainer",
  components: {
    UserStoragePathViewer,
  },
  props: {
    selectedDataProductUris: {
      type: Array,
      default: () => [],
    },
  },
  data() {
    return {
      userStoragePath: null,
    };
  },
  computed: {
    storagePath() {
      return ["~"].concat(this.userStoragePath.parts).join("/") + "/";
    },
  },
  created() {
    return this.loadUserStoragePath(mostRecentPath);
  },
  methods: {
    loadUserStoragePath(path) {
      return services.UserStoragePathService.get({
        path,
      }).then((result) => (this.userStoragePath = result));
    },
    directorySelected(path) {
      mostRecentPath = "~/" + path;
      return this.loadUserStoragePath(mostRecentPath);
    },
    fileSelected(file) {
      this.$emit("file-selected", file.data_product_uri);
    },
  },
};
</script>
