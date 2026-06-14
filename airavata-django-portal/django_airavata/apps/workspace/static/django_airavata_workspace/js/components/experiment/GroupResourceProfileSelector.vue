<template>
  <div>
    <div class="space-y-1.5">
      <Label for="group-resource-profile">Allocation</Label>
      <select
        id="group-resource-profile"
        v-model="groupResourceProfileId"
        required
        :class="nativeSelectClass"
        @change="groupResourceProfileChanged($event.target.value)"
      >
        <option :value="null" disabled>Select an allocation</option>
        <option
          v-for="option in groupResourceProfileOptions"
          :key="option.value"
          :value="option.value"
        >
          {{ option.text }}
        </option>
      </select>
    </div>
  </div>
</template>

<script>
import { services } from "django-airavata-api";
import { NATIVE_SELECT_CLASS } from "../../lib/utils";

export default {
  name: "group-resource-profile-selector",
  props: {
    value: {
      type: String,
    },
  },
  data() {
    return {
      groupResourceProfileId: this.value,
      groupResourceProfiles: [],
      workspacePreferences: null,
    };
  },
  async mounted() {
    await this.loadWorkspacePreferences();
    await this.loadGroupResourceProfiles();
    this.validate();
  },
  computed: {
    nativeSelectClass() {
      // Native option-driven select styled to match a shadcn <Input>.
      return NATIVE_SELECT_CLASS;
    },
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
    valid() {
      return !!this.groupResourceProfileId;
    },
  },
  methods: {
    loadGroupResourceProfiles: function () {
      return services.GroupResourceProfileService.list().then(
        (groupResourceProfiles) => {
          this.groupResourceProfiles = groupResourceProfiles;
          if (
            (!this.value ||
              !this.selectedValueInGroupResourceProfileList(
                groupResourceProfiles,
              )) &&
            this.groupResourceProfiles &&
            this.groupResourceProfiles.length > 0
          ) {
            // automatically select the last one user selected
            this.groupResourceProfileId =
              this.workspacePreferences.most_recent_group_resource_profile_id;
            this.emitValueChanged();
          }
        },
      );
    },
    loadWorkspacePreferences() {
      return services.WorkspacePreferencesService.get().then(
        (workspacePreferences) =>
          (this.workspacePreferences = workspacePreferences),
      );
    },
    groupResourceProfileChanged: function (groupResourceProfileId) {
      this.groupResourceProfileId = groupResourceProfileId;
      this.emitValueChanged();
    },
    emitValueChanged: function () {
      this.validate();
      this.$emit("input", this.groupResourceProfileId);
    },
    selectedValueInGroupResourceProfileList(groupResourceProfiles) {
      return (
        groupResourceProfiles
          .map((grp) => grp.group_resource_profile_id)
          .indexOf(this.value) >= 0
      );
    },
    validate() {
      if (!this.valid) {
        this.$emit("invalid");
      } else {
        this.$emit("valid");
      }
    },
  },
  watch: {},
};
</script>

<style></style>
