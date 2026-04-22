<template>
  <a :href="viewData.url">{{ viewData.label }}</a>
</template>

<script setup lang="ts">
defineProps<{
  viewData: { url?: string; label?: string; [key: string]: unknown };
}>();
</script>
