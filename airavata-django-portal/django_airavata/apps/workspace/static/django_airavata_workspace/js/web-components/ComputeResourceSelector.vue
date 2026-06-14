<template>
  <div class="space-y-1.5">
    <label
      for="compute-resource"
      class="text-sm leading-none font-medium select-none"
      >Compute Resource</label
    >
    <select
      id="compute-resource"
      v-model="resourceHostId"
      required
      :disabled="disabled || computeResourceOptions.length === 0"
      class="h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-xs outline-none transition-[color,box-shadow] focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50 disabled:cursor-not-allowed disabled:opacity-50 dark:bg-input/30"
      @change="computeResourceChanged"
    >
      <option :value="null" disabled>Select a Compute Resource</option>
      <option
        v-for="option in computeResourceOptions"
        :key="option.value"
        :value="option.value"
      >
        {{ option.text }}
      </option>
    </select>
  </div>
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
