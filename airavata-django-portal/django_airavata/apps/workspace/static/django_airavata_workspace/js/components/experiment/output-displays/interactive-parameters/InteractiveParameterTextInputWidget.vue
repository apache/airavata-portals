<template>
  <div class="input-group">
    <input
      ref="textInput"
      class="form-control"
      :value="value"
      @input="currentValue = ($event.target as HTMLInputElement).value"
      @keydown.enter="enterKeyPressed"
    />
    <span class="input-group-text">
      <button class="btn btn-primary" :disabled="disabled" @click="submit">Submit</button>
    </span>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from "vue";

const props = defineProps<{
  value: string;
}>();

const emit = defineEmits<{
  input: [value: string];
}>();

const textInput = ref<HTMLInputElement | null>(null);
const currentValue = ref<string>(props.value);

const disabled = computed(() => currentValue.value === props.value);

function submit() {
  emit("input", currentValue.value);
}

function enterKeyPressed() {
  if (!disabled.value) {
    textInput.value?.blur();
    submit();
  }
}
</script>
