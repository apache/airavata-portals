<template>
  <div class="row">
    <div class="col">
      <div class="mb-3" label="Allocation" label-for="group-resource-profile">
        <select
          id="group-resource-profile"
          v-model="groupResourceProfileId"
          class="form-select"
          required
          @change="emitValueChanged"
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
  </div>
</template>

<script>
import { services } from "django-airavata-api";

export default {
  name: "GroupResourceProfileSelector",
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
        groupResourceProfileOptions.sort((a, b) => a.text.localeCompare(b.text));
        return groupResourceProfileOptions;
      } else {
        return [];
      }
    },
    valid() {
      return !!this.groupResourceProfileId;
    },
  },
  watch: {},
  async mounted() {
    await this.loadWorkspacePreferences();
    await this.loadGroupResourceProfiles();
    this.validate();
  },
  methods: {
    loadGroupResourceProfiles: function () {
      return services.ProjectResourceProfileService.list().then((groupResourceProfiles) => {
        this.groupResourceProfiles = groupResourceProfiles;
        if (
          (!this.value || !this.selectedValueInGroupResourceProfileList(groupResourceProfiles)) &&
          this.groupResourceProfiles &&
          this.groupResourceProfiles.length > 0
        ) {
          // automatically select the last one user selected
          this.groupResourceProfileId =
            this.workspacePreferences.most_recent_project_resource_profile_id;
          this.emitValueChanged();
        }
      });
    },
    loadWorkspacePreferences() {
      return services.WorkspacePreferencesService.get().then(
        (workspacePreferences) => (this.workspacePreferences = workspacePreferences),
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
        groupResourceProfiles.map((grp) => grp.group_resource_profile_id).indexOf(this.value) >= 0
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
};
</script>

<style></style>
