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
      :class="nativeSelectClass"
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
import { NATIVE_SELECT_CLASS } from "../lib/utils";

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
    nativeSelectClass() {
      // Native option-driven select styled to match a shadcn <Input>.
      return NATIVE_SELECT_CLASS;
    },
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
