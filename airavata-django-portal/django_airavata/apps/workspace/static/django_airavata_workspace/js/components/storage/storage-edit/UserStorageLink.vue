<template>
  <div>
    <a
      class="text-primary"
      :href="storageFileViewRouteUrl()"
      @click="showFilePreview($event)"
    >
      {{ fileName }}
    </a>
    <Dialog v-model:open="open">
      <DialogScrollContent class="w-[60vw] max-w-[800px]">
        <DialogHeader>
          <DialogTitle>{{ fileName }}</DialogTitle>
        </DialogHeader>
        <user-storage-file-edit-viewer
          :file-name="fileName"
          :data-product-uri="dataProductUri"
          :mime-type="mimeType"
          @file-content-changed="
            (fileContent) => $emit('file-content-changed', fileContent)
          "
        />
        <DialogFooter>
          <a
            class="text-primary"
            :href="storageFileViewRouteUrl()"
            target="_blank"
            >Open in a new window</a
          >
        </DialogFooter>
      </DialogScrollContent>
    </Dialog>
  </div>
</template>

<script>
import UserStorageFileEditViewer from "./UserStorageEditViewer";

export default {
  name: "user-storage-link",
  components: { UserStorageFileEditViewer },
  data() {
    return {
      open: false,
    };
  },
  props: {
    fileName: {
      required: true,
    },
    dataProductUri: {
      required: true,
    },
    mimeType: {
      required: true,
    },
    allowPreview: {
      default: true,
      required: false,
    },
  },
  methods: {
    showFilePreview(event) {
      if (this.allowPreview) {
        this.open = true;
        event.preventDefault();
      }
    },
    storageFileViewRouteUrl() {
      // This endpoint can handle XHR upload or a TUS uploadURL
      return `/workspace/storage/~?dataProductUri=${this.dataProductUri}`;
    },
  },
};
</script>
