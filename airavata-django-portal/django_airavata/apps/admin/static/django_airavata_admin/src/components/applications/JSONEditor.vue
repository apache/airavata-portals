<template>
  <textarea
    :id="id"
    v-model="jsonString"
    class="form-control"
    :rows="rows"
    :disabled="disabled"
    :state="state"
    @input="valueChanged"
  />
</template>

<script setup lang="ts">
import { ref, watch } from "vue";

const props = defineProps<{
  modelValue?: Record<string, unknown> | null;
  id?: string;
  rows?: number;
  disabled?: boolean;
}>();

const emit = defineEmits<{
  "update:modelValue": [value: Record<string, unknown> | null];
}>();

const state = ref<boolean | null>(null);

function formatJSON(value: Record<string, unknown>) {
  return JSON.stringify(value, null, 4);
}

const jsonString = ref<string | null>(
  props.modelValue ? formatJSON(props.modelValue) : null,
);

watch(
  () => props.modelValue,
  (newValue) => {
    jsonString.value = newValue ? formatJSON(newValue) : null;
  },
);

function valueChanged(event: Event) {
  const newValue = (event.target as HTMLTextAreaElement).value;
  try {
    if (newValue) {
      const parsedValue = JSON.parse(newValue) as Record<string, unknown>;
      emit("update:modelValue", parsedValue);
    } else {
      emit("update:modelValue", null);
    }
    state.value = true;
  } catch (e) {
    state.value = false;
  }
}
</script>
