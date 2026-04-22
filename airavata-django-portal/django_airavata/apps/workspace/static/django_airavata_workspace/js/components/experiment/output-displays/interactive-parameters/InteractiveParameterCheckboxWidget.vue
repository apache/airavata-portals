<template>
  <div class="form-check">
    <input
      class="form-check-input"
      type="checkbox"
      :checked="value"
      @input="$emit('input', $event)"
    />
  </div>
</template>

<script setup lang="ts">
defineProps<{
  value: boolean;
}>();

defineEmits<{
  input: [event: Event];
}>();
</script>
