<template>
  <div>
    <div class="user-storage-file-edit-viewer-status">
      <div class="user-storage-file-edit-viewer-status-message">
        <span v-if="editAvailable && !readOnly && saved">All the changes are saved.</span>
        <span v-if="editAvailable && !readOnly && !saved">Changes are not saved.</span>
      </div>
      <div class="user-storage-file-edit-viewer-status-actions">
        <UserStorageDownloadButton :data-product-uri="dataProductUri" :file-name="fileName" />
        <button
          v-if="editAvailable && !readOnly"
          class="btn"
          :disabled="saved"
          @click="fileContentChanged"
        >
          Save
        </button>
      </div>
    </div>
    <CodeEditor v-if="editAvailable" v-model="currentContent" :line-numbers="true" />
    <div v-else class="user-storage-file-edit-viewer-no-preview">
      Inline edit not available. Click the <strong>Download</strong> button to download the file.
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from "vue";
import { services, utils } from "django-airavata-api";
import CodeEditor from "django-airavata-common-ui/js/components/CodeEditor.vue";
import UserStorageDownloadButton from "./UserStorageDownloadButton.vue";

const MAX_EDIT_FILESIZE = 1024 * 1024;

const props = defineProps<{
  fileName: string;
  dataProductUri: string;
  mimeType: string;
  downloadUrl: string;
}>();

const emit = defineEmits<{
  "file-content-changed": [fileContent: string];
}>();

const currentContent = ref("");
const saved = ref(true);
interface DataProductLike {
  filesize: number;
  user_has_write_access: boolean;
}
const dataProduct = ref<DataProductLike | null>(null);
const contentLoaded = ref(false);

const editAvailable = computed(
  () => !dataProduct.value || dataProduct.value.filesize < MAX_EDIT_FILESIZE,
);
const userHasWriteAccess = computed(
  () => dataProduct.value && dataProduct.value.user_has_write_access,
);
const readOnly = computed(() => !userHasWriteAccess.value);

watch(currentContent, () => {
  if (contentLoaded.value) {
    saved.value = false;
  }
});

function fileContentChanged() {
  if (currentContent.value) {
    utils.FetchUtils.put(`/api/data-products?product-uri=${props.dataProductUri}`, {
      fileContentText: currentContent.value,
    }).then(() => {
      emit("file-content-changed", currentContent.value);
    });
  }
  saved.value = true;
}

function loadDataProduct() {
  return services.DataProductService.retrieve({
    lookup: props.dataProductUri,
  }).then((dp: unknown) => {
    dataProduct.value = dp as DataProductLike;
    return dp;
  });
}

function setFileContent() {
  loadDataProduct().then(() => {
    if (editAvailable.value) {
      utils.FetchUtils.get(props.downloadUrl, "", {
        ignoreErrors: false,
        showSpinner: true,
        responseType: "text",
      }).then((res: string) => {
        contentLoaded.value = false;
        currentContent.value = res;
        saved.value = true;
        contentLoaded.value = true;
      });
    }
  });
}

onMounted(() => {
  setFileContent();
});
</script>
