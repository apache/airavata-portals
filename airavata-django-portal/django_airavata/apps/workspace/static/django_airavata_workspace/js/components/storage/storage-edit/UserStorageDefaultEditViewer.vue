<template>
  <div>
    <div class="user-storage-file-edit-viewer-status">
      <div class="user-storage-file-edit-viewer-status-message"></div>
      <div class="user-storage-file-edit-viewer-status-actions">
        <UserStorageDownloadButton :data-product-uri="dataProductUri" :file-name="fileName" />
      </div>
    </div>
    <div class="user-storage-file-edit-viewer-no-preview">No preview available.</div>
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
