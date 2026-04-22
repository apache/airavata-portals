<template>
  <select class="form-select" :value="value" @change="$emit('input', ($event.target as HTMLSelectElement).value)">
    <option v-for="opt in options" :key="opt.value" :value="opt.value">
      {{ opt.text }}
    </option>
  </select>
</template>

<script setup lang="ts">
import { computed } from "vue";

interface ParameterOption {
  value: string;
  text: string;
}

interface SelectParameter {
  options: ParameterOption[];
  [key: string]: unknown;
}

const props = defineProps<{
  value: string;
  parameter: SelectParameter;
}>();

defineEmits<{
  input: [value: string];
}>();

const options = computed(() => props.parameter.options);
</script>
