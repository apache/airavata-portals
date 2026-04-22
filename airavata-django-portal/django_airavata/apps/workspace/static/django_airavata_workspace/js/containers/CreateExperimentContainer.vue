<template>
  <experiment-editor
    v-if="experiment"
    :experiment="experiment"
    :app-module="appModule"
    :app-interface="appInterface"
    @saved="handleSavedExperiment"
    @saved-and-launched="handleSavedAndLaunchedExperiment"
  >
    <template #title>
      <span>Create a New Experiment</span>
    </template>
  </experiment-editor>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { services } from "django-airavata-api";
import { notifications } from "django-airavata-common-ui";
import ExperimentEditor from "../components/experiment/ExperimentEditor.vue";
import urls from "../utils/urls";

import { formatShort } from "django-airavata-common-ui/js/utils/dates.js";

const props = defineProps<{
  appModuleId?: string;
  userInputValues?: Record<string, unknown> | null;
  experimentDataDir?: string | null;
}>();

// Convenience accessors
const appModuleId = () => props.appModuleId;
const userInputValues = () => props.userInputValues;
const experimentDataDir = () => props.experimentDataDir;

const experiment = ref<unknown>(null);
const appModule = ref<unknown>(null);
const appInterface = ref<unknown>(null);

onMounted(() => {
  const modId = appModuleId();
  if (!modId) return;
  const loadAppModule = services.ApplicationModuleService.retrieve(
    { lookup: modId },
    { ignoreErrors: true },
  );
  const loadAppInterface = services.ApplicationModuleService.getApplicationInterface(
    { lookup: modId },
    { ignoreErrors: true },
  );
  Promise.all([loadAppModule, loadAppInterface])
    .then(([mod, iface]: [unknown, unknown]) => {
      const typedMod = mod as { app_module_name: string };
      const typedIface = iface as {
        createExperiment(): unknown;
      };
      const exp = typedIface.createExperiment() as {
        experiment_name: string;
        experiment_inputs: Array<{ name: string; value: unknown }>;
        user_configuration_data: { experiment_data_dir: string };
      };
      exp.experiment_name = typedMod.app_module_name + " on " + formatShort(new Date());
      appModule.value = mod;
      appInterface.value = iface;
      const inputValues = userInputValues();
      if (inputValues) {
        Object.keys(inputValues).forEach((k) => {
          const experimentInput = exp.experiment_inputs.find((inp) => inp.name === k);
          if (experimentInput) {
            experimentInput.value = inputValues[k];
          }
        });
      }
      const dataDir = experimentDataDir();
      if (dataDir) {
        exp.user_configuration_data.experiment_data_dir = dataDir;
      }
      experiment.value = exp;
    })
    .catch((error: unknown) => {
      notifications.NotificationList.addError(error);
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
