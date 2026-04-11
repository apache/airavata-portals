<template>
  <span v-if="downloadURL">
    <a :href="downloadURL" class="action-link" :target="linkTarget">
      {{ filename }}
    </a>
  </span>
  <span v-else>{{ filename }}</span>
</template>

<script>
import { models } from "django-airavata-api";
export default {
  name: "data-product-viewer",
  props: {
    dataProduct: {
      type: models.DataProduct,
      required: true,
    },
    inputFile: {
      type: Boolean,
      default: false,
    },
    mimeType: {
      type: String,
    },
    openInNewWindow: {
      type: Boolean,
      default: false,
    },
  },
  computed: {
    filename() {
      if (this.inputFile) {
        // productName captures the user provided name of the file, which may
        // not match the name of the file on the storage system (for example,
        // because of file name collision)
        return this.dataProduct.productName;
      } else {
        return this.dataProduct.filename;
      }
    },
    downloadURL() {
      if (!this.dataProduct.download_url) {
        return null;
      } else if (this.mime_type) {
        return `${this.dataProduct.download_url}&mime-type=${encodeURIComponent(
          this.mime_type
        )}`;
      } else {
        return this.dataProduct.download_url;
      }
    },
    linkTarget() {
      return this.openInNewWindow ? "_blank" : "_self";
    },
  },
};
</script>
