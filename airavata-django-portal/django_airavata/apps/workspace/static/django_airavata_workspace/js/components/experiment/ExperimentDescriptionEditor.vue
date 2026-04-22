<template>
  <form-group v-if="isEditing" label="Experiment Description" label-for="experiment-description">
    <textarea
      id="experiment-description"
      ref="description"
      v-model="data"
      class="form-control"
      rows="3"
      maxlength="255"
    ></textarea>
    <div class="mt-1">
      <button class="btn btn-success btn-sm" @click="toggleEditing">Save description</button>
      <a title="Cancel editing" class="text-secondary ms-3" @click="cancelEditing">
        <i class="fas fa-times"></i>
        <span class="visually-hidden">Cancel editing</span>
      </a>
    </div>
  </form-group>
  <div v-else class="mb-3">
    <a class="d-inline-block text-body mb-1" @click="startEditing">
      <i class="fas fa-align-left"></i>
      <span v-if="data"> Edit the description</span>
      <span v-else> Add a description</span>
    </a>
    <div v-if="data" class="ms-3">
      {{ data }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, nextTick } from "vue";

const props = defineProps<{
  modelValue: string | null;
}>();

const emit = defineEmits<{
  "update:modelValue": [value: string | null];
}>();

const description = ref<HTMLTextAreaElement | null>(null);
const isEditing = ref(false);
const originalValue = ref<string | null>(props.modelValue ?? null);

// VModelMixin: local data synced with modelValue
const data = ref<string | null>(props.modelValue ?? null);

watch(
  () => props.modelValue,
  (newVal) => {
    data.value = newVal ?? null;
  },
);

watch(data, (newVal, oldVal) => {
  if (newVal !== oldVal) {
    emit("update:modelValue", newVal);
  }
});

function toggleEditing() {
  isEditing.value = !isEditing.value;
}

function startEditing() {
  originalValue.value = data.value;
  isEditing.value = true;
  nextTick(() => description.value?.focus());
}

function cancelEditing() {
  data.value = originalValue.value;
  isEditing.value = false;
}
</script>
