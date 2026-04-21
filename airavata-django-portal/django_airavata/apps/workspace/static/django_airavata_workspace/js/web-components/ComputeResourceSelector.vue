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

<script>
import store from "./store";
import { mapGetters } from "vuex";

export default {
  name: "ComputeResourceSelector",
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
  store: store,
  data() {
    return {
      resourceHostId: this.value,
    };
  },
  created() {
    this.$store.dispatch("loadComputeResourceNames");
  },
  computed: {
    computeResourceOptions: function () {
      const computeResourceIds = Object.keys(this.computeResourceNames).filter((crid) => {
        if (this.includedComputeResources) {
          return this.includedComputeResources.includes(crid);
        } else {
          return true;
        }
      });
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
    ...mapGetters(["computeResourceNames"]),
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
