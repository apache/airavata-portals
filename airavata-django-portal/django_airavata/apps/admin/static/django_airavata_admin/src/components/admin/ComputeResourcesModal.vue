<template>
  <!-- TODO: migrate to Bootstrap 5 modal -->
  <div
    ref="modal"
    class="modal"
    title="Select Compute Resource"
    :ok-disabled="modalSelectComputeResourceOkDisabled"
    @ok="onSelectComputeResource"
  >
    <select v-model="selectedComputeResource" class="form-select">
      <option :value="null">Please select compute resource</option>
      <option v-for="opt in computeResourceOptions" :key="opt.value" :value="opt.value">
        {{ opt.text }}
      </option>
    </select>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { services } from "django-airavata-api";

const props = defineProps<{
  computeResourceNames?: Array<{ host_id: string; host: string }>;
  excludedResourceIds?: string[];
}>();

const emit = defineEmits<{
  selected: [value: string | null];
}>();

const selectedComputeResource = ref<string | null>(null);
const localComputeResourceNames = ref<Array<{ host_id: string; host: string }> | null>(null);

const modalSelectComputeResourceOkDisabled = computed(
  () => selectedComputeResource.value === null || selectedComputeResource.value === undefined,
);

const computeResourceOptions = computed(() => {
  const names = props.computeResourceNames ? props.computeResourceNames : localComputeResourceNames.value;
  const options = names
    ? names
        .filter((comp) =>
          props.excludedResourceIds ? !props.excludedResourceIds.includes(comp.host_id) : true,
        )
        .map((comp) => {
          return {
            value: comp.host_id,
            text: comp.host,
          };
        })
    : [];
  options.sort((a, b) => a.text.toLowerCase().localeCompare(b.text.toLowerCase()));
  return options;
});

onMounted(() => {
  if (!props.computeResourceNames) {
    services.ComputeResourceService.namesList().then(
      (resourceNames: Array<{ host_id: string; host: string }>) =>
        (localComputeResourceNames.value = resourceNames),
    );
  }
});

function onSelectComputeResource() {
  emit("selected", selectedComputeResource.value);
}

// TODO: migrate to Bootstrap 5 Modal.show()
function show() {
  // no-op until Bootstrap 5 modal migration is complete
}

defineExpose({ show });
</script>
