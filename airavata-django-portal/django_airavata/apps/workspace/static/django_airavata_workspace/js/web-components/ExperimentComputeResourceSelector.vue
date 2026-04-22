<template>
  <div>
    <compute-resource-selector
      :value="resourceHostId"
      :disabled="disabled"
      :included-compute-resources="computeResources"
      @input.stop="computeResourceChanged"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, watch, getCurrentInstance } from "vue";
import ComputeResourceSelector from "./ComputeResourceSelector.vue";
import { useWebComponentsStore } from "django-airavata-common-ui/js/stores/webComponents";

const props = withDefaults(defineProps<{
  value?: string | null;
  applicationModuleId: string;
  disabled?: boolean;
}>(), {
  value: null,
  disabled: false,
});

const webComponentsStore = useWebComponentsStore();

const computeResources = computed(() => webComponentsStore.computeResources as unknown as string[] | null);
const resourceHostId = computed(() => webComponentsStore.resourceHostId as unknown as string | null);

function emitValueChanged(hostId: string | null) {
  const instance = getCurrentInstance();
  const el = instance?.proxy?.$el as Element | undefined;
  if (el) {
    const inputEvent = new CustomEvent("input", {
      detail: [hostId],
      composed: true,
      bubbles: true,
    });
    el.dispatchEvent(inputEvent);
  }
}

function computeResourceChanged(event: CustomEvent) {
  const [newResourceHostId] = event.detail as [string | null];
  if (newResourceHostId) {
    webComponentsStore.updateComputeResourceHostId({
      resourceHostId: newResourceHostId,
    });
  }
  emitValueChanged(newResourceHostId);
}

watch(() => props.value, (value) => {
  if (value && value !== resourceHostId.value) {
    webComponentsStore.updateComputeResourceHostId({
      resourceHostId: value ?? "",
    });
  }
});

// Initialize
webComponentsStore.initializeComputeResources({
  applicationModuleId: props.applicationModuleId,
  resourceHostId: props.value,
});
</script>

<style lang="scss">
@import "./styles";
:host {
  display: block;
}
</style>
