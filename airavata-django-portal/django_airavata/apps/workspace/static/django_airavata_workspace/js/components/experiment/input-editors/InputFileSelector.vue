<template>
  <div v-if="isSelectingFile">
    <user-storage-file-selection-container
      @file-selected="fileSelected"
      @cancel="cancelFileSelection"
      :selected-data-product-uris="selectedDataProductURIs"
    />
  </div>
  <div class="flex items-center" v-else>
    <Button
      variant="outline"
      @click="isSelectingFile = true"
      class="input-file-option"
      >Select file from storage</Button
    >
    <span class="mx-3 text-muted-foreground">OR</span>
    <uppy
      class="input-file-option"
      ref="uppy"
      xhr-upload-endpoint="/api/upload"
      tus-upload-finish-endpoint="/api/tus-upload-finish"
      @upload-success="uploadSuccess"
      @upload-started="$emit('uploadstart')"
      @upload-finished="uploadFinished"
      :multiple="multiple"
    />
  </div>
</template>

<script>
import { models } from "django-airavata-api";
import { components } from "django-airavata-common-ui";
import UserStorageFileSelectionContainer from "../../storage/UserStorageFileSelectionContainer";

export default {
  name: "input-file-selector",
  props: {
    multiple: {
      type: Boolean,
      default: false,
    },
    selectedDataProductURIs: {
      type: Array,
      default: () => [],
    },
  },
  components: {
    UserStorageFileSelectionContainer,
    uppy: components.Uppy,
  },
  computed: {},
  data() {
    return {
      isSelectingFile: false,
    };
  },
  created() {},
  methods: {
    unselect() {
      this.file = null;
    },
    fileSelected(dataProductURI) {
      this.isSelectingFile = false;
      this.$emit("selected", dataProductURI);
    },
    cancelFileSelection() {
      this.isSelectingFile = false;
      this.unselect();
    },
    uploadSuccess(result) {
      const dataProduct = new models.DataProduct(result["data-product"]);
      this.$emit("selected", dataProduct.product_uri, dataProduct);
    },
    uploadFinished() {
      this.$emit("uploadend");
      this.$refs.uppy.reset();
    },
  },
};
</script>

<style scoped>
.input-file-option {
  flex: 1 1 50%;
}
</style>
