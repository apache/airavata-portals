<template>
  <span :class="['badge', 'bg-' + badgeVariant]">{{ statusName }}</span>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { models } from "django-airavata-api";

const props = defineProps<{
  statusName: string;
}>();

const experimentState = computed(() => models.ExperimentState.byName(props.statusName));

const badgeVariant = computed(() => {
  if (experimentState.value.isProgressing) {
    return "secondary";
  } else if (experimentState.value === models.ExperimentState.COMPLETED) {
    return "success";
  } else if (
    experimentState.value === models.ExperimentState.CANCELING ||
    experimentState.value === models.ExperimentState.CANCELED
  ) {
    return "warning";
  } else if (experimentState.value === models.ExperimentState.FAILED) {
    return "danger";
  } else {
    return "info";
  }
});
</script>
