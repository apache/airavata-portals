<template>
  <div class="row mb-1 align-items-center">
    <label class="col-md-3 col-form-label" :for="`scalar-${descriptor.name}`">
      <code>{{ descriptor.name }}</code>
      <span class="text-muted small ms-1">{{ descriptor.type }}</span>
    </label>
    <div class="col-md-9">
      <select
        v-if="descriptor.type === 'enum'"
        :id="`scalar-${descriptor.name}`"
        :data-test="`scalar-${descriptor.name}`"
        class="form-select"
        :value="modelValue ?? ''"
        @change="emit('update:modelValue', ($event.target as HTMLSelectElement).value)"
      >
        <option value="" disabled>Choose…</option>
        <option v-for="o in descriptor.options ?? []" :key="o" :value="o">{{ o }}</option>
      </select>
      <input
        v-else
        :id="`scalar-${descriptor.name}`"
        :data-test="`scalar-${descriptor.name}`"
        class="form-control"
        :type="inputType"
        :value="modelValue ?? ''"
        @input="onInput(($event.target as HTMLInputElement).value)"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import type { IODescriptor, ScalarValue } from "django-airavata-common-ui/js/stores/launch-types";

const props = defineProps<{ descriptor: IODescriptor; modelValue: ScalarValue | null }>();
const emit = defineEmits<{ "update:modelValue": [v: ScalarValue | null] }>();

const inputType = computed(() => {
  switch (props.descriptor.type) {
    case "int":
    case "float":
      return "number";
    case "bool":
      return "checkbox";
    default:
      return "text";
  }
});

function onInput(raw: string) {
  if (props.descriptor.type === "int") emit("update:modelValue", raw === "" ? null : Number.parseInt(raw, 10));
  else if (props.descriptor.type === "float") emit("update:modelValue", raw === "" ? null : Number.parseFloat(raw));
  else emit("update:modelValue", raw);
}
</script>
