<template>
  <b-form-group :label="label" label-for="group-resource-profile">
    <b-form-select
      id="group-resource-profile"
      :model-value="groupResourceProfileId"
      :options="groupResourceProfileOptions"
      required
      @change="groupResourceProfileChanged"
      :disabled="disabled"
    >
      <template #first>
        <option :value="null" disabled>
          <slot name="null-option">Select an allocation</slot>
        </option>
      </template>
    </b-form-select>
  </b-form-group>
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
