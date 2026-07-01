<template>
  <experiment-editor
    v-if="experiment"
    :experiment="experiment"
    :app-module="appModule"
    :app-interface="appInterface"
    @saved="handleSavedExperiment"
    @savedAndLaunched="handleSavedAndLaunchedExperiment"
  >
    <template #title><span>Create a New Experiment</span></template>
  </experiment-editor>
</template>

<script>
import { services } from "django-airavata-api";
import { notifications } from "django-airavata-common-ui";
import ExperimentEditor from "../components/experiment/ExperimentEditor.vue";
import urls from "../utils/urls";

import dayjs from "dayjs";
import localizedFormat from "dayjs/plugin/localizedFormat";

dayjs.extend(localizedFormat);

export default {
  name: "create-experiment-container",
  props: ["appModuleId", "userInputValues", "experimentDataDir"],
  data() {
    return {
      experiment: null,
      appModule: null,
      appInterface: null,
    };
  },
  components: {
    "experiment-editor": ExperimentEditor,
  },
  methods: {
    handleSavedExperiment: function () {
      // Redirect to experiment view
      urls.navigateToExperimentsList();
    },
    handleSavedAndLaunchedExperiment: function (experiment) {
      // Redirect to experiment view
      urls.navigateToViewExperiment(experiment, { launching: true });
    },
  },
  computed: {},
  mounted: function () {
    const loadAppModule = services.ApplicationModuleService.retrieve(
      { lookup: this.appModuleId },
      { ignoreErrors: true },
    );
    const loadAppInterface =
      services.ApplicationModuleService.getApplicationInterface(
        { lookup: this.appModuleId },
        { ignoreErrors: true },
      );
    Promise.all([loadAppModule, loadAppInterface])
      .then(([appModule, appInterface]) => {
        const experiment = appInterface.createExperiment();
        experiment.experiment_name =
          appModule.app_module_name + " on " + dayjs().format("lll");
        this.appModule = appModule;
        this.appInterface = appInterface;
        if (this.userInputValues) {
          Object.keys(this.userInputValues).forEach((k) => {
            const experimentInput = experiment.experiment_inputs.find(
              (inp) => inp.name === k,
            );
            if (experimentInput) {
              experimentInput.value = this.userInputValues[k];
            }
          });
        }
        if (this.experimentDataDir) {
          experiment.user_configuration_data.experiment_data_dir =
            this.experimentDataDir;
        }
        this.experiment = experiment;
      })
      .catch((error) => {
        notifications.NotificationList.addError(error);
      });
  },
};
</script>
<style>
/* style the containing div, in base.html template */
.main-content-wrapper {
  background-color: #ffffff;
}
</style>
