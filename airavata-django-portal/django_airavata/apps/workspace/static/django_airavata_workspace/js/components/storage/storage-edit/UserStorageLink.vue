<template>
  <div>
    <a :href="storageFileViewRouteUrl()" @click="showFilePreview($event)">
      {{ fileName }}
    </a>
    <!-- TODO: Replace b-modal with Bootstrap 5 modal -->
    <div ref="modal" class="modal" :title="fileName" scrollable size="lg" static lazy>
      <UserStorageFileEditViewer
        :file-name="fileName"
        :data-product-uri="dataProductUri"
        :mime-type="mimeType"
        @file-content-changed="(fileContent) => emit('file-content-changed', fileContent)"
      />
      <div class="modal-footer">
        <a :href="storageFileViewRouteUrl()" target="_blank">Open in a new window</a>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import UserStorageFileEditViewer from "./UserStorageEditViewer.vue";

const props = withDefaults(
  defineProps<{
    fileName: string;
    dataProductUri: string;
    mimeType: string;
    allowPreview?: boolean;
  }>(),
  { allowPreview: true },
);

const emit = defineEmits<{
  "file-content-changed": [fileContent: string];
}>();

const modal = ref<HTMLElement & { show?: () => void } | null>(null);

function showFilePreview(event: MouseEvent) {
  if (props.allowPreview) {
    modal.value?.show?.();
    event.preventDefault();
  }
}

function storageFileViewRouteUrl() {
  return `/resources/storage/~?dataProductUri=${props.dataProductUri}`;
}
</script>
