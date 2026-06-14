<template>
  <div>
    <compute-resource-selector
      :value="resourceHostId"
      :disabled="disabled"
      :includedComputeResources="computeResources"
      @input="computeResourceChanged"
    />
  </div>
</template>

<script>
import { mapState } from "pinia";
import { useExperimentStore } from "./store";
import ComputeResourceSelector from "./ComputeResourceSelector.vue";

export default {
  name: "experiment-compute-resource-selector",
  props: {
    value: {
      type: String,
      default: null,
    },
    applicationModuleId: {
      type: String,
      required: true,
    },
    disabled: {
      type: Boolean,
      default: false,
    },
  },
  created() {
    useExperimentStore().initializeComputeResources({
      applicationModuleId: this.applicationModuleId,
      resourceHostId: this.value,
    });
  },
  components: {
    ComputeResourceSelector,
  },
  computed: {
    ...mapState(useExperimentStore, {
      // compute resources for the current set of application deployments
      computeResources: "computeResources",
      resourceHostId: "getResourceHostId",
      groupResourceProfileId: "getGroupResourceProfileId",
    }),
  },
  methods: {
    computeResourceChanged(event) {
      const [resourceHostId] = event.detail;
      useExperimentStore().updateComputeResourceHostId({
        resourceHostId,
      });
      this.emitValueChanged(resourceHostId);
    },
    emitValueChanged(resourceHostId) {
      const inputEvent = new CustomEvent("input", {
        detail: [resourceHostId],
        composed: true,
        bubbles: true,
      });
      this.$el.dispatchEvent(inputEvent);
    },
  },
  watch: {
    value(value) {
      if (value && value !== this.resourceHostId) {
        useExperimentStore().updateComputeResourceHostId({
          resourceHostId: value,
        });
      }
    },
  },
};
</script>

<style lang="scss">
@import "./styles";
:host {
  display: block;
}
</style>
