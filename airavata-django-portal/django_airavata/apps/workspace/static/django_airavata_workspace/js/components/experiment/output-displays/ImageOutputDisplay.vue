<template>
  <img v-if="dataUrl" :src="dataUrl" />
</template>

<script setup lang="ts">
import { computed } from "vue";

const props = defineProps<{
  viewData: Record<string, unknown>;
}>();

const dataUrl = computed(() => {
  if (props.viewData && props.viewData.image) {
    return `data:${props.viewData["mime-type"]};base64,${props.viewData["image"]}`;
  } else {
    return null;
  }
});
</script>
