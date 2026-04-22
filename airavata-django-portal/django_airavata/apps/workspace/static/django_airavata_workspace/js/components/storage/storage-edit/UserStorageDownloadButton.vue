<template>
  <button class="btn" :href="downloadUrl" :download="fileName">Download</button>
</template>

<script setup lang="ts">
import { computed } from "vue";

const props = defineProps<{
  fileName: string;
  dataProductUri: string;
}>();

const downloadUrl = computed(() => `/sdk/download/?data-product-uri=${props.dataProductUri}`);
</script>
