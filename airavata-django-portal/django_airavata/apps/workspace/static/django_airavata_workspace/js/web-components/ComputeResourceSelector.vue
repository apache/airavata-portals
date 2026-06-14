<template>
  <b-form-group label="Compute Resource" label-for="compute-resource">
    <b-form-select
      id="compute-resource"
      v-model="resourceHostId"
      :options="computeResourceOptions"
      required
      @update:model-value="computeResourceChanged"
      :disabled="disabled || computeResourceOptions.length === 0"
    >
      <template #first>
        <option :value="null" disabled>Select a Compute Resource</option>
      </template>
    </b-form-select>
  </b-form-group>
</template>

<script>
import { mapState } from "pinia";
import { useExperimentStore } from "./store";

export default {
  name: "compute-resource-selector",
  props: {
    value: {
      // compute resource host id
      type: String,
      default: null,
    },
    includedComputeResources: {
      type: Array,
      default: null,
    },
    disabled: {
      type: Boolean,
      default: false,
    },
  },
  data() {
    return {
      resourceHostId: this.value,
    };
  },
  created() {
    useExperimentStore().loadComputeResourceNames();
  },
  computed: {
    ...mapState(useExperimentStore, ["computeResourceNames"]),
    computeResourceOptions: function () {
      const computeResourceIds = Object.keys(this.computeResourceNames).filter(
        (crid) => {
          if (this.includedComputeResources) {
            return this.includedComputeResources.includes(crid);
          } else {
            return true;
          }
        },
      );
      const computeResourceOptions = computeResourceIds.map((computeHostId) => {
        return {
          value: computeHostId,
          text:
            computeHostId in this.computeResourceNames
              ? this.computeResourceNames[computeHostId]
              : "",
        };
      });
      computeResourceOptions.sort((a, b) => a.text.localeCompare(b.text));
      return computeResourceOptions;
    },
  },
  methods: {
    computeResourceChanged() {
      this.emitValueChanged();
    },
    emitValueChanged: function () {
      const inputEvent = new CustomEvent("input", {
        detail: [this.resourceHostId],
        composed: true,
        bubbles: true,
      });
      this.$el.dispatchEvent(inputEvent);
    },
  },
  watch: {
    value() {
      this.resourceHostId = this.value;
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
