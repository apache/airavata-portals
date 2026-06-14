import { defineStore } from "pinia";
import { errors, models, services } from "django-airavata-api";
import ExperimentState from "django-airavata-api/static/django_airavata_api/js/models/ExperimentState";
import JobState from "django-airavata-api/static/django_airavata_api/js/models/JobState";

function getDataProducts(io, collection) {
  if (!io.value || !collection) {
    return [];
  }
  let dataProducts;
  if (io.type === models.DataType.URI_COLLECTION) {
    const dataProductURIs = io.value.split(",");
    dataProducts = dataProductURIs.map((uri) =>
      collection.find((dp) => dp.product_uri === uri),
    );
  } else {
    const dataProductURI = io.value;
    dataProducts = collection.filter((dp) => dp.product_uri === dataProductURI);
  }
  return dataProducts ? dataProducts.filter((dp) => (dp ? true : false)) : [];
}

// Pinia store replacing the Vuex `viewExperiment` namespaced module. Pinia has no
// mutations, so the former mutations are folded into actions (state assignment is
// done directly on `this`). Getters are preserved as Pinia getters.
export const useViewExperimentStore = defineStore("viewExperiment", {
  state: () => ({
    fullExperiment: null,
    launching: false,
    polling: false,
    clonedExperiment: null,
    runningIntermediateOutputFetches: {},
    applicationInterface: null,
    groupResourceProfile: null,
  }),
  getters: {
    isPolling: (state) => state.polling,
    experimentId: (state) =>
      state.fullExperiment ? state.fullExperiment.experiment_id : null,
    experiment: (state) =>
      state.fullExperiment ? state.fullExperiment.experiment : null,
    isExecuting() {
      return (
        this.experiment &&
        this.experiment.latestStatus &&
        this.experiment.latestStatus.state === ExperimentState.EXECUTING
      );
    },
    isFinished() {
      return this.experiment && this.experiment.isFinished;
    },
    finishedOrExecuting() {
      return (
        this.experiment && (this.experiment.isFinished || this.isExecuting)
      );
    },
    outputDataProducts(state) {
      const result = {};
      if (state.fullExperiment && state.fullExperiment.output_data_products) {
        state.fullExperiment.experiment.experiment_outputs.forEach((output) => {
          result[output.name] = getDataProducts(
            output,
            state.fullExperiment.output_data_products,
          );
        });
      }
      return result;
    },
    // getter that derives a map of output names and whether they are currently executing
    currentlyRunningIntermediateOutputFetches(state) {
      const result = {};
      if (this.experiment) {
        for (const output of this.experiment.experiment_outputs) {
          const runningIntermediateOutputFetchTimestamp =
            state.runningIntermediateOutputFetches[output.name];
          const processStatus = output.intermediate_output
            ? output.intermediate_output.process_status
            : null;
          const processStatusTimestamp = processStatus
            ? processStatus.time_of_state_change
            : null;
          result[output.name] = false;
          // If our most recent timestamp for the intermediate output is the
          // request to fetch it, the assume it is currently running
          if (
            runningIntermediateOutputFetchTimestamp &&
            (!processStatusTimestamp ||
              processStatusTimestamp < runningIntermediateOutputFetchTimestamp)
          ) {
            result[output.name] = true;
          }
          // intermediate output fetch is still running if process isn't finished
          else if (processStatus) {
            result[output.name] = !processStatus.isFinished;
          }
        }
      }
      return result;
    },
    userHasWriteAccess() {
      return this.experiment ? this.experiment.user_has_write_access : false;
    },
    isJobActive(state) {
      return (
        state.fullExperiment &&
        state.fullExperiment.job_details &&
        state.fullExperiment.job_details.some(
          (job) =>
            job.latestJobStatus &&
            job.latestJobStatus.job_state === JobState.ACTIVE,
        )
      );
    },
    showQueueSettings(state) {
      return state.applicationInterface
        ? state.applicationInterface.show_queue_settings
        : false;
    },
    groupResourceProfileId() {
      return this.experiment?.user_configuration_data
        ?.group_resource_profile_id;
    },
  },
  actions: {
    async setInitialFullExperimentData({ fullExperimentData }) {
      const fullExperiment = await services.FullExperimentService.retrieve({
        lookup: fullExperimentData.experiment_id,
        initialFullExperimentData: fullExperimentData,
      });
      await this.setFullExperiment({ fullExperiment });
    },
    async setFullExperiment({ fullExperiment }) {
      this.fullExperiment = fullExperiment;
      const appInterfaceId = fullExperiment.experiment.execution_id;
      try {
        const applicationInterface =
          await services.ApplicationInterfaceService.retrieve(
            { lookup: appInterfaceId },
            { ignoreErrors: true },
          );
        this.applicationInterface = applicationInterface;
      } catch (error) {
        // Ignore when application interface is not found; it was probably deleted
        // But in all other cases, report the error as unhandled
        if (!errors.ErrorUtils.isNotFoundError(error)) {
          errors.UnhandledErrorDispatcher.reportUnhandledError(error);
        }
      }
      this.loadGroupResourceProfile();
      this.initPollingExperiment();
    },
    setLaunching({ launching }) {
      this.launching = launching;
      if (launching) {
        this.initPollingExperiment();
      }
    },
    async loadExperiment({ experimentId, showSpinner = false }) {
      const fullExperiment = await services.FullExperimentService.retrieve(
        { lookup: experimentId },
        { ignoreErrors: true, showSpinner },
      );
      this.fullExperiment = fullExperiment;
    },
    async pollExperiment() {
      if (!this.fullExperiment) {
        this.polling = false;
        return;
      }
      if (
        (this.launching && !this.fullExperiment.experiment.hasLaunched) ||
        this.fullExperiment.experiment.isProgressing
      ) {
        try {
          await this.loadExperiment({
            experimentId: this.fullExperiment.experiment_id,
          });
          setTimeout(() => {
            this.pollExperiment();
          }, 3000);
        } catch {
          // Wait 30 seconds after an error and then try again
          setTimeout(() => {
            this.pollExperiment();
          }, 30000);
        }
      } else {
        this.polling = false;
      }
    },
    initPollingExperiment() {
      // Only start polling if we aren't already polling
      if (!this.isPolling) {
        this.polling = true;
        this.pollExperiment();
      }
    },
    async clone() {
      const clonedExperiment = await services.ExperimentService.clone({
        lookup: this.experimentId,
      });
      this.clonedExperiment = clonedExperiment;
    },
    async launch() {
      try {
        await services.ExperimentService.launch({
          lookup: this.experimentId,
        });
        this.setLaunching({ launching: true });
      } catch (error) {
        // Surface launch failures to the user instead of silently swallowing them.
        errors.UnhandledErrorDispatcher.reportUnhandledError(error);
      }
    },
    async cancel() {
      await services.ExperimentService.cancel({
        lookup: this.experimentId,
      });
      this.loadExperiment({ experimentId: this.experimentId });
    },
    async submitFetchIntermediateOutputs({ outputNames }) {
      await services.ExperimentService.fetchIntermediateOutputs({
        lookup: this.experimentId,
        data: {
          outputNames,
        },
      });
      // add an entry for each output name in a runningIntermediateOutputFetches, with timestamp
      for (const outputName of outputNames) {
        this.runningIntermediateOutputFetches = {
          ...this.runningIntermediateOutputFetches,
          [outputName]: new Date(),
        };
      }
    },
    async loadGroupResourceProfile() {
      const groupResourceProfile =
        await services.GroupResourceProfileService.retrieve({
          lookup: this.groupResourceProfileId,
        });
      this.groupResourceProfile = groupResourceProfile;
    },
  },
});

export default useViewExperimentStore;
