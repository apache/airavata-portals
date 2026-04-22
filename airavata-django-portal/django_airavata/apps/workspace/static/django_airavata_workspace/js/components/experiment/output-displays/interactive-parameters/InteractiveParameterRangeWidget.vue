<template>
  <div>
    <input
      ref="rangeInput"
      class="form-control"
      type="range"
      :value="value"
      :min="parameter.min"
      :max="parameter.max"
      :step="parameter.step || 'any'"
      @input="updateValue"
      @mouseup="mouseUp"
      @keyup="keyUp"
    />
    <small>Value: {{ roundedValue }}</small>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from "vue";

interface InteractiveParameter {
  min?: number;
  max?: number;
  step?: number;
  [key: string]: unknown;
}

const props = defineProps<{
  value: number;
  parameter: InteractiveParameter;
}>();

const emit = defineEmits<{
  input: [value: number];
}>();

const rangeInput = ref<HTMLInputElement | null>(null);
const currentValue = ref<number>(parseFloat(String(props.value)));

const initialValue = computed(() => parseFloat(String(props.value)));
const disabled = computed(() => currentValue.value === initialValue.value);
const roundedValue = computed(() =>
  currentValue.value ? currentValue.value.toFixed(2) : null,
);

function updateValue(event: Event) {
  currentValue.value = parseFloat((event.target as HTMLInputElement).value);
}

function submit() {
  emit("input", currentValue.value);
}

function mouseUp() {
  rangeInput.value?.blur();
  if (!disabled.value) {
    submit();
  }
}

function keyUp() {}
</script>
