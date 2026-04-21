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

<script>
import store from "./store";
import { mapGetters } from "vuex";
import ComputeResourceSelector from "./ComputeResourceSelector.vue";

export default {
  name: "ExperimentComputeResourceSelector",
  components: {
    ComputeResourceSelector,
  },
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
    this.$store.dispatch("initializeComputeResources", {
      applicationModuleId: this.applicationModuleId,
      resourceHostId: this.value,
    });
  },
  store: store,
  computed: {
    ...mapGetters([
      // compute resources for the current set of application deployments
      "computeResources",
      "resourceHostId",
      "groupResourceProfileId",
    ]),
  },
  methods: {
    computeResourceChanged(event) {
      const [resourceHostId] = event.detail;
      this.$store.dispatch("updateComputeResourceHostId", {
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
        this.$store.dispatch("updateComputeResourceHostId", {
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
