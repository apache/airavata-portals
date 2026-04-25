<template>
  <div class="text-muted small mb-2">
    Invocation: <code>{{ command }}</code>
  </div>
</template>

<script setup lang="ts">
defineProps<{ command: string }>();
</script>
