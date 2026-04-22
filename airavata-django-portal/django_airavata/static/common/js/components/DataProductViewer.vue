<template>
  <span v-if="downloadURL">
    <a :href="downloadURL" class="action-link" :target="linkTarget">
      {{ filename }}
    </a>
  </span>
  <span v-else>{{ filename }}</span>
</template>

<script setup lang="ts">
import { computed } from "vue";

interface DataProduct {
  productName?: string;
  filename?: string;
  download_url?: string;
  [key: string]: unknown;
}

const props = withDefaults(defineProps<{
  dataProduct: DataProduct;
  inputFile?: boolean;
  mimeType?: string;
  openInNewWindow?: boolean;
}>(), {
  inputFile: false,
  mimeType: undefined,
  openInNewWindow: false,
});

const filename = computed(() => {
  if (props.inputFile) {
    // productName captures the user provided name of the file, which may
    // not match the name of the file on the storage system (for example,
    // because of file name collision)
    return props.dataProduct.productName;
  } else {
    return props.dataProduct.filename;
  }
});

const downloadURL = computed(() => {
  if (!props.dataProduct.download_url) {
    return null;
  } else if (props.mimeType) {
    return `${props.dataProduct.download_url}&mime-type=${encodeURIComponent(props.mimeType)}`;
  } else {
    return props.dataProduct.download_url;
  }
});

const linkTarget = computed(() => (props.openInNewWindow ? "_blank" : "_self"));
</script>
