<template>
  <div class="row g-2">
    <div class="col-md-3">
      <label class="form-label small">Compute resource</label>
      <select
        data-test="cr"
        class="form-select form-select-sm"
        :value="modelValue.compute_resource_id ?? ''"
        @change="onCR(($event.target as HTMLSelectElement).value)"
      >
        <option value="" disabled>Choose…</option>
        <option v-for="cr in profile.compute_resources" :key="cr.compute_resource_id" :value="cr.compute_resource_id">
          {{ cr.name }}
        </option>
      </select>
    </div>
    <div class="col-md-3">
      <label class="form-label small">Partition</label>
      <select
        data-test="partition"
        class="form-select form-select-sm"
        :disabled="!partitions.length"
        :value="modelValue.partition ?? ''"
        @change="emit('update:modelValue', { ...modelValue, partition: ($event.target as HTMLSelectElement).value })"
      >
        <option value="" disabled>Choose…</option>
        <option v-for="p in partitions" :key="p.name" :value="p.name">{{ p.name }}</option>
      </select>
    </div>
    <div class="col-md-2">
      <label class="form-label small">Walltime</label>
      <input
        data-test="walltime"
        class="form-control form-control-sm"
        :value="modelValue.walltime"
        @input="emit('update:modelValue', { ...modelValue, walltime: ($event.target as HTMLInputElement).value })"
      />
    </div>
    <div class="col-md-2">
      <label class="form-label small">Nodes</label>
      <input
        type="number" min="1"
        data-test="nodes"
        class="form-control form-control-sm"
        :value="modelValue.nodes"
        @input="emit('update:modelValue', { ...modelValue, nodes: Number(($event.target as HTMLInputElement).value) })"
      />
    </div>
    <div class="col-md-2">
      <label class="form-label small">CPUs / node</label>
      <input
        type="number" min="1"
        data-test="cpus"
        class="form-control form-control-sm"
        :value="modelValue.cpus_per_node"
        @input="emit('update:modelValue', { ...modelValue, cpus_per_node: Number(($event.target as HTMLInputElement).value) })"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import type { ResourceProfile, RuntimeChoice } from "django-airavata-common-ui/js/stores/launch-types";

const props = defineProps<{ profile: ResourceProfile; modelValue: RuntimeChoice }>();
const emit = defineEmits<{ "update:modelValue": [v: RuntimeChoice] }>();

const partitions = computed(() => {
  if (!props.modelValue.compute_resource_id) return [];
  const cr = props.profile.compute_resources.find(
    (c) => c.compute_resource_id === props.modelValue.compute_resource_id,
  );
  return cr?.partitions ?? [];
});

function onCR(id: string) {
  emit("update:modelValue", { ...props.modelValue, compute_resource_id: id, partition: null });
}
</script>
