<template>
  <span :class="{ 'font-italic': notAvailable }">{{ applicationName }}</span>
</template>
<script setup lang="ts">
import { ref, computed, watch, onMounted } from "vue";
import { errors, services, utils } from "django-airavata-api";

const props = defineProps<{
  applicationInterfaceId: string;
}>();

const applicationInterface = ref<{ application_name: string } | null>(null);
const notAvailable = ref(false);

const applicationName = computed(() => {
  if (notAvailable.value) {
    return "N/A";
  } else {
    return applicationInterface.value ? applicationInterface.value.application_name : "";
  }
});

watch(
  () => props.applicationInterfaceId,
  () => loadApplicationInterface(),
);

onMounted(() => {
  loadApplicationInterface();
});

function loadApplicationInterface(): void {
  services.ApplicationInterfaceService.retrieve(
    { lookup: props.applicationInterfaceId },
    { ignoreErrors: true, cache: true },
  )
    .then((appInterface: { application_name: string }) => (applicationInterface.value = appInterface))
    .catch((error: unknown) => {
      if (errors.ErrorUtils.isNotFoundError(error)) {
        notAvailable.value = true;
      } else {
        throw error;
      }
    })
    .catch(utils.FetchUtils.reportError);
}
</script>
