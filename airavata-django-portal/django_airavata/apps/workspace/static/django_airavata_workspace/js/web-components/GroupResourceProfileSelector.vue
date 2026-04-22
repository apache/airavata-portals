<template>
  <div class="mb-3" :label="label" label-for="group-resource-profile">
    <select
      id="group-resource-profile"
      class="form-select"
      :value="groupResourceProfileId"
      required
      :disabled="disabled"
      @change="groupResourceProfileChanged(($event.target as HTMLInputElement).value)"
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

<script setup lang="ts">
import { computed, watch, getCurrentInstance } from "vue";
import { useWebComponentsStore } from "django-airavata-common-ui/js/stores/webComponents";

interface GroupResourceProfile {
  groupResourceProfileId: string;
  groupResourceProfileName: string;
}

interface ProfileOption {
  value: string;
  text: string;
}

const props = withDefaults(defineProps<{
  value?: string | null;
  label?: string;
  disabled?: boolean;
}>(), {
  value: null,
  label: "Allocation",
  disabled: false,
});

const webComponentsStore = useWebComponentsStore();

const groupResourceProfileId = computed(() => webComponentsStore.groupResourceProfileId as unknown as string | null);
const groupResourceProfiles = computed(() => webComponentsStore.groupResourceProfiles as unknown as GroupResourceProfile[] | null);

const groupResourceProfileOptions = computed<ProfileOption[]>(() => {
  if (groupResourceProfiles.value && groupResourceProfiles.value.length > 0) {
    const options = groupResourceProfiles.value.map((grp) => ({
      value: grp.groupResourceProfileId,
      text: grp.groupResourceProfileName,
    }));
    options.sort((a, b) => a.text.localeCompare(b.text));
    return options;
  } else {
    return [];
  }
});

function emitValueChanged() {
  const instance = getCurrentInstance();
  const el = instance?.proxy?.$el as Element | undefined;
  if (el) {
    const inputEvent = new CustomEvent("input", {
      detail: [groupResourceProfileId.value],
      composed: true,
      bubbles: true,
    });
    el.dispatchEvent(inputEvent);
  }
}

function groupResourceProfileChanged(newProfileId: string) {
  webComponentsStore.updateGroupResourceProfileId({
    groupResourceProfileId: newProfileId,
  });
}

watch(groupResourceProfileId, () => {
  emitValueChanged();
});

watch(() => props.value, (newValue) => {
  if ((newValue ?? null) !== groupResourceProfileId.value) {
    webComponentsStore.updateGroupResourceProfileId({
      groupResourceProfileId: newValue ?? "",
    });
  }
});

// Initialize
webComponentsStore.initializeGroupResourceProfileId({
  groupResourceProfileId: props.value ?? "",
});
webComponentsStore.loadGroupResourceProfiles();
</script>

<style lang="scss">
@import "./styles";
:host {
  display: block;
}
</style>
