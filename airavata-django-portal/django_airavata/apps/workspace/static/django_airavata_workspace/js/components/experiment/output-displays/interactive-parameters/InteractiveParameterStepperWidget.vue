<template>
  <div class="input-group">
    <input
      ref="textInput"
      class="form-control"
      type="number"
      :value="value"
      :min="parameter.min"
      :max="parameter.max"
      :step="parameter.step || 'any'"
      @input="updateValue"
      @keydown.enter="enterKeyPressed"
    />
    <span class="input-group-text">
      <button class="btn btn-primary" :disabled="disabled" @click="submit">Submit</button>
    </span>
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
  valid: [];
  invalid: [message: string];
}>();

const textInput = ref<HTMLInputElement | null>(null);
const currentValue = ref<number>(parseFloat(String(props.value)));
const valid = ref(false);

const disabled = computed(
  () => !valid.value || currentValue.value === parseFloat(String(props.value)),
);

function updateValue(event: Event) {
  let newValue = parseFloat((event.target as HTMLInputElement).value);
  if (props.parameter && props.parameter.max !== null && props.parameter.max !== undefined) {
    newValue = Math.min(props.parameter.max, newValue);
  }
  if (props.parameter && props.parameter.min !== null && props.parameter.min !== undefined) {
    newValue = Math.max(props.parameter.min, newValue);
  }
  currentValue.value = newValue;
  if (textInput.value?.validity.valid) {
    valid.value = true;
    emit("valid");
  } else {
    valid.value = false;
    emit("invalid", textInput.value?.validationMessage ?? "");
  }
}

function submit() {
  if (!disabled.value) {
    emit("input", currentValue.value);
  }
}

function enterKeyPressed() {
  if (!disabled.value) {
    textInput.value?.blur();
    submit();
  }
}
</script>
