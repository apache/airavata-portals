<template>
  <UserStorageTextEditViewer
    v-if="isText"
    :file-name="fileName"
    :data-product-uri="dataProductUri"
    :mime-type="mimeType"
    :download-url="downloadUrl"
    @file-content-changed="(fileContent) => emit('file-content-changed', fileContent)"
  />
  <UserStorageImageEditViewer
    v-else-if="isImage"
    :file-name="fileName"
    :data-product-uri="dataProductUri"
    :mime-type="mimeType"
    :download-url="downloadUrl"
    @file-content-changed="(fileContent) => emit('file-content-changed', fileContent)"
  />
  <UserStorageAudioEditViewer
    v-else-if="isAudio"
    :file-name="fileName"
    :data-product-uri="dataProductUri"
    :mime-type="mimeType"
    :download-url="downloadUrl"
    @file-content-changed="(fileContent) => emit('file-content-changed', fileContent)"
  />
  <UserStorageVideoEditViewer
    v-else-if="isVideo"
    :file-name="fileName"
    :data-product-uri="dataProductUri"
    :mime-type="mimeType"
    :download-url="downloadUrl"
    @file-content-changed="(fileContent) => emit('file-content-changed', fileContent)"
  />
  <UserStoragePdfEditViewer
    v-else-if="isPdf"
    :file-name="fileName"
    :data-product-uri="dataProductUri"
    :mime-type="mimeType"
    :download-url="downloadUrl"
    @file-content-changed="(fileContent) => emit('file-content-changed', fileContent)"
  />
  <UserStorageDefaultEditViewer
    v-else
    :file-name="fileName"
    :data-product-uri="dataProductUri"
    :mime-type="mimeType"
    :download-url="downloadUrl"
    @file-content-changed="(fileContent) => emit('file-content-changed', fileContent)"
  />
</template>

<script setup lang="ts">
import { computed } from "vue";
import UserStorageTextEditViewer from "./UserStorageTextEditViewer.vue";
import UserStorageImageEditViewer from "./UserStorageImageEditViewer.vue";
import UserStorageDefaultEditViewer from "./UserStorageDefaultEditViewer.vue";
import UserStorageAudioEditViewer from "./UserStorageAudioEditViewer.vue";
import UserStorageVideoEditViewer from "./UserStorageVideoEditViewer.vue";
import UserStoragePdfEditViewer from "./UserStoragePdfEditViewer.vue";

const props = defineProps<{
  fileName: string;
  dataProductUri: string;
  mimeType: string;
}>();

const emit = defineEmits<{
  "file-content-changed": [fileContent: string];
}>();

const downloadUrl = computed(
  () => `/sdk/download/?data-product-uri=${props.dataProductUri}`,
);

const isText = computed(() => /text\/.*/.test(props.mimeType));
const isImage = computed(() => /image\/.*/.test(props.mimeType));
const isAudio = computed(() => /audio\/.*/.test(props.mimeType));
const isVideo = computed(() => /video\/.*/.test(props.mimeType));
const isPdf = computed(() => /pdf/.test(props.mimeType));
</script>

<style>
.user-storage-file-edit-viewer-status {
  display: flex;
  padding-bottom: 10px;
}

.user-storage-file-edit-viewer-status .user-storage-file-edit-viewer-status-message {
  flex: 1;
  color: #919191;
  font-size: 14px;
}

.user-storage-file-edit-viewer-status .user-storage-file-edit-viewer-status-actions button,
.user-storage-file-edit-viewer-status .user-storage-file-edit-viewer-status-actions a {
  margin-right: 3px;
  margin-left: 3px;
}

.user-storage-file-edit-viewer-no-preview {
  font-size: 36px;
  color: #c0c4c7;
  text-align: center;
  padding: 20px;
}
</style>
