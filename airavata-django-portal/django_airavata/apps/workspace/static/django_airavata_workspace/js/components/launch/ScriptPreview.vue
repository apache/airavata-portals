<template>
  <pre class="bg-dark text-light p-3 rounded small mb-0" style="overflow-x: auto;"><code>{{ script }}</code></pre>
</template>

<script setup lang="ts">
defineProps<{ script: string }>();
</script>
