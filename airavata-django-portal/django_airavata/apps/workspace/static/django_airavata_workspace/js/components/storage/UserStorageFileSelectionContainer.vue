<template>
  <Card>
    <CardHeader class="border-b">
      <CardTitle class="text-base">Select a file</CardTitle>
    </CardHeader>
    <CardContent>
      <user-storage-path-viewer
        v-if="userStoragePath"
        :user-storage-path="userStoragePath"
        :storage-path="storagePath"
        @directory-selected="directorySelected"
        @file-selected="fileSelected"
        :include-delete-action="false"
        :include-select-file-action="true"
        :include-create-file-action="false"
        :include-download-action="false"
        :download-in-new-window="true"
        :selected-data-product-uris="selectedDataProductUris"
      >
      </user-storage-path-viewer>
    </CardContent>
    <CardFooter class="border-t">
      <div class="flex w-full justify-end">
        <a
          href="#"
          class="text-muted-foreground"
          @click.prevent="$emit('cancel')"
          >Cancel</a
        >
      </div>
    </CardFooter>
  </Card>
</template>

<script>
import { services } from "django-airavata-api";
import UserStoragePathViewer from "./UserStoragePathViewer";

// Keep track of most recent path so that when user needs to select an
// additional file they are taken back to the last path
let mostRecentPath = "~";

export default {
  name: "user-storage-file-selection-container",
  computed: {
    storagePath() {
      return ["~"].concat(this.userStoragePath.parts).join("/") + "/";
    },
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
  components: {
    UserStoragePathViewer,
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
