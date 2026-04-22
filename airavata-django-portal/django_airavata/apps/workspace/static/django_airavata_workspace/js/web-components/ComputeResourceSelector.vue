<template>
  <div class="mb-3" label="Compute Resource" label-for="compute-resource">
    <select
      id="compute-resource"
      v-model="resourceHostId"
      class="form-select"
      required
      :disabled="disabled || computeResourceOptions.length === 0"
      @change="computeResourceChanged"
      @input.stop
    >
      <option :value="null" disabled>Select a Compute Resource</option>
      <option v-for="opt in computeResourceOptions" :key="opt.value" :value="opt.value">
        {{ opt.text }}
      </option>
    </select>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, getCurrentInstance } from "vue";
import { useWebComponentsStore } from "django-airavata-common-ui/js/stores/webComponents";

interface ComputeResourceOption {
  value: string;
  text: string;
}

const props = withDefaults(defineProps<{
  value?: string | null;
  includedComputeResources?: string[] | null;
  disabled?: boolean;
}>(), {
  value: null,
  includedComputeResources: null,
  disabled: false,
});

const webComponentsStore = useWebComponentsStore();

const resourceHostId = ref<string | null>(props.value ?? null);

const computeResourceNames = computed(() =>
  webComponentsStore.computeResourceNames as unknown as Record<string, string>
);

const computeResourceOptions = computed<ComputeResourceOption[]>(() => {
  const computeResourceIds = Object.keys(computeResourceNames.value).filter((crid) => {
    if (props.includedComputeResources) {
      return props.includedComputeResources.includes(crid);
    } else {
      return true;
    }
  });
  const options = computeResourceIds.map((computeHostId) => ({
    value: computeHostId,
    text:
      computeHostId in computeResourceNames.value
        ? computeResourceNames.value[computeHostId]
        : "",
  }));
  options.sort((a, b) => a.text.localeCompare(b.text));
  return options;
});

function emitValueChanged() {
  const instance = getCurrentInstance();
  const el = instance?.proxy?.$el as Element | undefined;
  if (el) {
    const inputEvent = new CustomEvent("input", {
      detail: [resourceHostId.value],
      composed: true,
      bubbles: true,
    });
    el.dispatchEvent(inputEvent);
  }
}

function computeResourceChanged() {
  emitValueChanged();
}

watch(() => props.value, () => {
  resourceHostId.value = props.value ?? null;
});

webComponentsStore.loadComputeResourceNames();
</script>

<style lang="scss">
@import "./styles";
:host {
  display: block;
}
</style>
