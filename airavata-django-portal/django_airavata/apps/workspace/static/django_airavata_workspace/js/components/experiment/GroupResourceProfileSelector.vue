<template>
  <div>
    <div class="space-y-1.5">
      <Label for="group-resource-profile">Allocation</Label>
      <select
        id="group-resource-profile"
        v-model="groupResourceProfileId"
        required
        class="h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-xs outline-none transition-[color,box-shadow] focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50 disabled:cursor-not-allowed disabled:opacity-50 dark:bg-input/30"
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
