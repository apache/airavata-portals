<template>
  <div>
    <div class="user-storage-file-edit-viewer-status">
      <div class="user-storage-file-edit-viewer-status-message"></div>
      <div class="user-storage-file-edit-viewer-status-actions">
        <user-storage-download-button :data-product-uri="dataProductUri" :file-name="fileName" />
      </div>
    </div>
    <audio controls style="width: 100%">
      <source :src="downloadUrl" />
    </audio>
  </div>
</template>

<script setup lang="ts">
import UserStorageDownloadButton from "./UserStorageDownloadButton.vue";

defineProps<{
  fileName: string;
  dataProductUri: string;
  mimeType: string;
  downloadUrl: string;
}>();
</script>
