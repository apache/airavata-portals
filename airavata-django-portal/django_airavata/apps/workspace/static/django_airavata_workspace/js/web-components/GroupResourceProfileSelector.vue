<template>
  <div class="space-y-1.5">
    <label
      for="group-resource-profile"
      class="text-sm leading-none font-medium select-none"
      >{{ label }}</label
    >
    <select
      id="group-resource-profile"
      :value="groupResourceProfileId"
      required
      :disabled="disabled"
      class="h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-xs outline-none transition-[color,box-shadow] focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50 disabled:cursor-not-allowed disabled:opacity-50 dark:bg-input/30"
      @change="groupResourceProfileChanged($event.target.value)"
    >
      <option :value="null" disabled>
        <slot name="null-option">Select an allocation</slot>
      </option>
      <option
        v-for="option in groupResourceProfileOptions"
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
  name: "group-resource-profile-selector",
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
  created() {
    const store = useExperimentStore();
    store.initializeGroupResourceProfileId({
      groupResourceProfileId: this.value,
    });
    store.loadGroupResourceProfiles();
  },
  computed: {
    ...mapState(useExperimentStore, {
      groupResourceProfileId: "getGroupResourceProfileId",
      groupResourceProfiles: "groupResourceProfiles",
    }),
    groupResourceProfileOptions: function () {
      if (this.groupResourceProfiles && this.groupResourceProfiles.length > 0) {
        const groupResourceProfileOptions = this.groupResourceProfiles.map(
          (groupResourceProfile) => {
            return {
              value: groupResourceProfile.group_resource_profile_id,
              text: groupResourceProfile.group_resource_profile_name,
            };
          },
        );
        groupResourceProfileOptions.sort((a, b) =>
          a.text.localeCompare(b.text),
        );
        return groupResourceProfileOptions;
      } else {
        return [];
      }
    },
  },
  methods: {
    groupResourceProfileChanged: function (groupResourceProfileId) {
      useExperimentStore().updateGroupResourceProfileId({
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
        useExperimentStore().updateGroupResourceProfileId({
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
