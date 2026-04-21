<template>
  <button class="btn" :href="downloadUrl" :download="fileName">Download</button>
</template>

<script>
export default {
  name: "UserStorageDownloadButton",
  props: {
    fileName: {
      required: true,
    },
    dataProductUri: {
      required: true,
    },
  },
  computed: {
    downloadUrl() {
      return `/sdk/download/?data-product-uri=${this.dataProductUri}`;
    },
  },
};
</script>
