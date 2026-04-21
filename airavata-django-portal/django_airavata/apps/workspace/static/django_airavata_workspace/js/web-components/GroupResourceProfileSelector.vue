<template>
  <div class="mb-3" :label="label" label-for="group-resource-profile">
    <select
      id="group-resource-profile"
      class="form-select"
      :value="groupResourceProfileId"
      required
      :disabled="disabled"
      @change="groupResourceProfileChanged($event.target.value)"
      @input.stop
    >
      <option :value="null" disabled>
        <slot name="null-option">Select an allocation</slot>
      </option>
      <option v-for="opt in groupResourceProfileOptions" :key="opt.value" :value="opt.value">
        {{ opt.text }}
      </option>
    </select>
  </div>
</template>

<script>
import store from "./store";
import { mapGetters } from "vuex";

export default {
  name: "GroupResourceProfileSelector",
  props: {
    value: {
      type: String,
      default: null,
    },
    label: {
      type: String,
      default: "Allocation",
    },
    disabled: {
      type: Boolean,
      default: false,
    },
  },
  store: store,
  created() {
    this.$store.dispatch("initializeGroupResourceProfileId", {
      groupResourceProfileId: this.value,
    });
    this.$store.dispatch("loadGroupResourceProfiles");
  },
  computed: {
    ...mapGetters(["groupResourceProfileId", "groupResourceProfiles"]),
    groupResourceProfileOptions: function () {
      if (this.groupResourceProfiles && this.groupResourceProfiles.length > 0) {
        const groupResourceProfileOptions = this.groupResourceProfiles.map(
          (groupResourceProfile) => {
            return {
              value: groupResourceProfile.groupResourceProfileId,
              text: groupResourceProfile.groupResourceProfileName,
            };
          },
        );
        groupResourceProfileOptions.sort((a, b) => a.text.localeCompare(b.text));
        return groupResourceProfileOptions;
      } else {
        return [];
      }
    },
  },
  methods: {
    groupResourceProfileChanged: function (groupResourceProfileId) {
      this.$store.dispatch("updateGroupResourceProfileId", {
        groupResourceProfileId,
      });
    },
    emitValueChanged: function () {
      const inputEvent = new CustomEvent("input", {
        detail: [this.groupResourceProfileId],
        composed: true,
        bubbles: true,
      });
      this.$el.dispatchEvent(inputEvent);
    },
  },
  watch: {
    value(newValue) {
      if (newValue !== this.groupResourceProfileId) {
        this.$store.dispatch("updateGroupResourceProfileId", {
          groupResourceProfileId: newValue,
        });
      }
    },
    groupResourceProfileId() {
      this.emitValueChanged();
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
