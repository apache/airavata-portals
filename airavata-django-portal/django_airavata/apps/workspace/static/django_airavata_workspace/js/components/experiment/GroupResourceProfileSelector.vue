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

<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { services } from "django-airavata-api";

interface GroupResourceProfile {
  group_resource_profile_id: string;
  group_resource_profile_name: string;
}

interface WorkspacePreferences {
  most_recent_project_resource_profile_id?: string;
}

const props = defineProps<{
  modelValue?: string | null;
}>();

const emit = defineEmits<{
  "update:modelValue": [value: string | null];
  valid: [];
  invalid: [];
}>();

const groupResourceProfileId = ref<string | null>(props.modelValue ?? null);
const groupResourceProfiles = ref<GroupResourceProfile[]>([]);
const workspacePreferences = ref<WorkspacePreferences | null>(null);

const groupResourceProfileOptions = computed(() => {
  if (groupResourceProfiles.value.length > 0) {
    const options = groupResourceProfiles.value.map((grp) => ({
      value: grp.group_resource_profile_id,
      text: grp.group_resource_profile_name,
    }));
    options.sort((a, b) => a.text.localeCompare(b.text));
    return options;
  }
  return [];
});

const valid = computed(() => !!groupResourceProfileId.value);

function emitValueChanged() {
  validate();
  emit("update:modelValue", groupResourceProfileId.value);
}

function validate() {
  if (!valid.value) {
    emit("invalid");
  } else {
    emit("valid");
  }
}

function selectedValueInGroupResourceProfileList(profiles: GroupResourceProfile[]) {
  return profiles.map((grp) => grp.group_resource_profile_id).indexOf(props.modelValue ?? "") >= 0;
}

function loadGroupResourceProfiles() {
  return services.ProjectResourceProfileService.list().then(
    (profiles: GroupResourceProfile[]) => {
      groupResourceProfiles.value = profiles;
      if (
        (!props.modelValue || !selectedValueInGroupResourceProfileList(profiles)) &&
        groupResourceProfiles.value.length > 0
      ) {
        // automatically select the last one user selected
        groupResourceProfileId.value =
          workspacePreferences.value?.most_recent_project_resource_profile_id ?? null;
        emitValueChanged();
      }
    },
  );
}

function loadWorkspacePreferences() {
  return services.WorkspacePreferencesService.get().then(
    (prefs: WorkspacePreferences) => (workspacePreferences.value = prefs),
  );
}

onMounted(async () => {
  await loadWorkspacePreferences();
  await loadGroupResourceProfiles();
  validate();
});
</script>

<style></style>
