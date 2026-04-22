<template>
  <div v-if="isSelectingFile">
    <UserStorageFileSelectionContainer
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
    <Uppy
      ref="uppyRef"
      class="input-file-option"
      xhr-upload-endpoint="/api/upload"
      tus-upload-finish-endpoint="/api/tus-upload-finish"
      :multiple="multiple"
      @upload-success="uploadSuccess"
      @upload-started="emit('uploadstart')"
      @upload-finished="uploadFinished"
    />
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { models } from "django-airavata-api";
import { components } from "django-airavata-common-ui";
import UserStorageFileSelectionContainer from "../../storage/UserStorageFileSelectionContainer.vue";

const Uppy = components.Uppy;

type DataProduct = InstanceType<typeof models.DataProduct>;

withDefaults(
  defineProps<{
    multiple?: boolean;
    selectedDataProductURIs?: string[];
  }>(),
  {
    multiple: false,
    selectedDataProductURIs: () => [],
  },
);

const emit = defineEmits<{
  selected: [dataProductUri: string, dataProduct?: DataProduct];
  uploadstart: [];
  uploadend: [];
}>();

const isSelectingFile = ref(false);
const uppyRef = ref<{ reset: () => void } | null>(null);

function fileSelected(dataProductURI: string) {
  isSelectingFile.value = false;
  emit("selected", dataProductURI);
}

function cancelFileSelection() {
  isSelectingFile.value = false;
}

function uploadSuccess(result: Record<string, unknown>) {
  const dataProduct = new models.DataProduct(result["data-product"] as Record<string, unknown>);
  emit("selected", dataProduct.productUri as string, dataProduct);
}

function uploadFinished() {
  emit("uploadend");
  uppyRef.value?.reset();
}
</script>

<style scoped>
.input-file-option {
  flex: 1 1 50%;
}
</style>
