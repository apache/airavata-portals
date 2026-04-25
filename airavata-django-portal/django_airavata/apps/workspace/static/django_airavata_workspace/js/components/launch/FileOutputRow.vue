<template>
  <div class="d-flex align-items-center gap-2 border rounded p-2 mb-1">
    <div class="flex-shrink-0" style="width: 140px;">
      <code>{{ descriptor.name }}</code>
      <span class="text-muted small ms-1">{{ descriptor.type }}</span>
    </div>
    <select
      class="form-select form-select-sm"
      style="width: 160px;"
      :data-test="`file-out-storage-${descriptor.name}`"
      :value="modelValue?.storage_id ?? ''"
      @change="onStorage(($event.target as HTMLSelectElement).value)"
    >
      <option value="" disabled>Storage…</option>
      <option v-for="s in storages" :key="s.storage_id" :value="s.storage_id">{{ s.name }}</option>
    </select>
    <input
      class="form-control form-control-sm flex-grow-1"
      :data-test="`file-out-path-${descriptor.name}`"
      :value="modelValue?.path ?? ''"
      placeholder="/path/to/output"
      @input="onPath(($event.target as HTMLInputElement).value)"
    />
    <span class="badge bg-info text-dark">stage-out</span>
  </div>
</template>

<script setup lang="ts">
import type { IODescriptor, StorageRef, UserStorage } from "django-airavata-common-ui/js/stores/launch-types";

const props = defineProps<{
  descriptor: IODescriptor;
  modelValue: StorageRef | null;
  storages: UserStorage[];
}>();
const emit = defineEmits<{ "update:modelValue": [v: StorageRef] }>();

function onStorage(id: string) {
  emit("update:modelValue", { storage_id: id, path: props.modelValue?.path ?? "" });
}
function onPath(p: string) {
  emit("update:modelValue", { storage_id: props.modelValue?.storage_id ?? "", path: p });
}
</script>
