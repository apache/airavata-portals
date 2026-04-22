<template>
  <experiment-editor
    v-if="appModule"
    :experiment="experiment"
    :app-module="appModule"
    :app-interface="appInterface"
    @saved="handleSavedExperiment"
    @saved-and-launched="handleSavedAndLaunchedExperiment"
  >
    <template #title>
      <span>Edit Experiment</span>
    </template>
  </experiment-editor>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { errors, services } from "django-airavata-api";
import { notifications } from "django-airavata-common-ui";
import ExperimentEditor from "../components/experiment/ExperimentEditor.vue";
import urls from "../utils/urls";

const props = defineProps<{
  experimentId: string;
}>();

const experiment = ref<unknown>(null);
const appModule = ref<unknown>(null);
const appInterface = ref<unknown>(null);

onMounted(() => {
  services.ExperimentService.retrieve({ lookup: props.experimentId })
    .then((exp: unknown) => {
      experiment.value = exp;
      const appInterfaceId = (exp as { execution_id: string }).execution_id;
      return services.ApplicationInterfaceService.retrieve(
        { lookup: appInterfaceId },
        { ignoreErrors: true },
      );
    })
    .then((iface: unknown) => {
      appInterface.value = iface;
      const appModuleId = (iface as { application_modules: string[] }).application_modules[0];
      return services.ApplicationModuleService.retrieve({ lookup: appModuleId });
    })
    .then((mod: unknown) => {
      appModule.value = mod;
    })
    .catch((error: unknown) => {
      const exp = experiment.value as { execution_id: string } | null;
      const message = errors.ErrorUtils.isNotFoundError(error)
        ? `Application interface (${exp?.execution_id}) was not found.
           If it has been deleted then you won't be able to edit this experiment.`
        : `Unable to load application interface (${exp?.execution_id}) or module`;
      notifications.NotificationList.add(
        new notifications.Notification({
          type: "ERROR",
          message,
        }),
      );
    });
});

function handleSavedExperiment() {
  urls.navigateToExperimentsList("");
}

function handleSavedAndLaunchedExperiment(exp: unknown) {
  urls.navigateToViewExperiment("", exp as { experiment_id: string }, { launching: true });
}
</script>

<style>
/* style the containing div, in base.html template */
.main-content-wrapper {
  background-color: #ffffff;
}
</style>
