<template>
  <div v-if="isSelectingFile">
    <user-storage-file-selection-container
      :selected-data-product-uris="selectedDataProductURIs"
      @file-selected="fileSelected"
      @cancel="cancelFileSelection"
    />
  </div>
  <div v-else class="d-flex align-items-center">
    <button class="btn input-file-option" @click="isSelectingFile = true">
      Select file from storage
    </button>
    <span class="text-muted mx-3">OR</span>
    <uppy
      ref="uppy"
      class="input-file-option"
      xhr-upload-endpoint="/api/upload"
      tus-upload-finish-endpoint="/api/tus-upload-finish"
      :multiple="multiple"
      @upload-success="uploadSuccess"
      @upload-started="$emit('uploadstart')"
      @upload-finished="uploadFinished"
    />
  </div>
</template>

<script>
import { models } from "django-airavata-api";
import { components } from "django-airavata-common-ui";
import UserStorageFileSelectionContainer from "../../storage/UserStorageFileSelectionContainer";

export default {
  name: "InputFileSelector",
  components: {
    UserStorageFileSelectionContainer,
    uppy: components.Uppy,
  },
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
  data() {
    return {
      isSelectingFile: false,
    };
  },
  computed: {},
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
      this.$emit("selected", dataProduct.productUri, dataProduct);
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
