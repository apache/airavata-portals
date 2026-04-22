/**
 * Pinia experiment store — ports the "view-experiment" Vuex module from:
 *   apps/workspace/static/django_airavata_workspace/js/store/modules/view-experiment.js
 *
 * Covers: polling, launch, cancel, clone, intermediate output fetches,
 * application interface, and group resource profile resolution.
 *
 * Vuex module stays in place for M3; this store coexists. Consumer migration
 * happens in M4.
 */

import { defineStore } from "pinia";
import { ref, computed } from "vue";
import { errors, models, services } from "django-airavata-api";
import type {
  FullExperiment,
  ApplicationInterface,
  GroupResourceProfile,
  RunningIntermediateOutputFetches,
} from "../types/experiment";

// ---------------------------------------------------------------------------
// Helpers — re-implemented from the Vuex module's local function
// ---------------------------------------------------------------------------

type DataType = typeof models.DataType;

function getDataProducts(
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  io: any,
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  collection: any[] | undefined,
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
): any[] {
  if (!io.value || !collection) return [];
  let dataProducts: (typeof collection)[number][] | null = null;
  const DataType = models.DataType as unknown as DataType;
  if (io.type === (DataType as unknown as { URI_COLLECTION: string }).URI_COLLECTION) {
    const uris = (io.value as string).split(",");
    dataProducts = uris.map((uri: string) =>
      collection.find((dp: Record<string, unknown>) => dp["product_uri"] === uri),
    );
  } else {
    dataProducts = collection.filter(
      (dp: Record<string, unknown>) => dp["product_uri"] === io.value,
    );
  }
  return dataProducts ? dataProducts.filter(Boolean) : [];
}

// ---------------------------------------------------------------------------
// Store definition
// ---------------------------------------------------------------------------

export const useExperimentStore = defineStore("experiment", () => {
  // ---------------------------------------------------------------------------
  // State
  // ---------------------------------------------------------------------------
  const fullExperiment = ref<FullExperiment | null>(null);
  const launching = ref<boolean>(false);
  const polling = ref<boolean>(false);
  const clonedExperiment = ref<Record<string, unknown> | null>(null);
  const runningIntermediateOutputFetches = ref<RunningIntermediateOutputFetches>({});
  const applicationInterface = ref<ApplicationInterface | null>(null);
  const groupResourceProfile = ref<GroupResourceProfile | null>(null);

  // ---------------------------------------------------------------------------
  // Getters
  // ---------------------------------------------------------------------------
  const isPolling = computed(() => polling.value);

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const experimentId = computed<string | null>(() =>
    fullExperiment.value ? (fullExperiment.value as any)["experiment_id"] : null,
  );

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const experiment = computed<any | null>(() =>
    fullExperiment.value ? (fullExperiment.value as any)["experiment"] : null,
  );

  const isExecuting = computed<boolean>(() => {
    if (!experiment.value || !experiment.value.latestStatus) return false;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const ExperimentState = (models as any).ExperimentState;
    return (
      ExperimentState &&
      experiment.value.latestStatus.state === ExperimentState.EXECUTING
    );
  });

  const isFinished = computed<boolean>(
    () => !!experiment.value && !!experiment.value.isFinished,
  );

  const finishedOrExecuting = computed<boolean>(
    () => !!experiment.value && (!!experiment.value.isFinished || isExecuting.value),
  );

  const outputDataProducts = computed<Record<string, unknown[]>>(() => {
    const result: Record<string, unknown[]> = {};
    const fe = fullExperiment.value as any;
    if (fe && fe.output_data_products) {
      fe.experiment.experiment_outputs.forEach((output: any) => {
        result[output.name] = getDataProducts(output, fe.output_data_products);
      });
    }
    return result;
  });

  const currentlyRunningIntermediateOutputFetches = computed<Record<string, boolean>>(() => {
    const result: Record<string, boolean> = {};
    if (!experiment.value) return result;
    for (const output of experiment.value.experiment_outputs ?? []) {
      const requestTimestamp = runningIntermediateOutputFetches.value[output.name];
      const processStatus = output.intermediate_output?.process_status ?? null;
      const processStatusTimestamp = processStatus?.time_of_state_change ?? null;
      result[output.name] = false;
      if (
        requestTimestamp &&
        (!processStatusTimestamp || processStatusTimestamp < requestTimestamp)
      ) {
        result[output.name] = true;
      } else if (processStatus) {
        result[output.name] = !processStatus.isFinished;
      }
    }
    return result;
  });

  const userHasWriteAccess = computed<boolean>(() =>
    experiment.value ? !!experiment.value.user_has_write_access : false,
  );

  const isJobActive = computed<boolean>(() => {
    const fe = fullExperiment.value as any;
    if (!fe || !fe.job_details) return false;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const JobState = (models as any).JobState;
    return fe.job_details.some(
      (job: any) => job.latestJobStatus && job.latestJobStatus.jobState === (JobState?.ACTIVE),
    );
  });

  const showQueueSettings = computed<boolean>(() =>
    applicationInterface.value
      ? !!(applicationInterface.value as any)["show_queue_settings"]
      : false,
  );

  const groupResourceProfileId = computed<string | null>(
    () =>
      (experiment.value as any)?.user_configuration_data?.group_resource_profile_id ?? null,
  );

  // ---------------------------------------------------------------------------
  // Actions
  // ---------------------------------------------------------------------------

  async function setInitialFullExperimentData({
    fullExperimentData,
  }: {
    fullExperimentData: Record<string, unknown>;
  }): Promise<void> {
    const fe = (await services.FullExperimentService.retrieve({
      lookup: fullExperimentData["experiment_id"],
      initialFullExperimentData: fullExperimentData,
    })) as FullExperiment;
    await setFullExperiment({ fullExperiment: fe });
  }

  async function setFullExperiment({
    fullExperiment: fe,
  }: {
    fullExperiment: FullExperiment;
  }): Promise<void> {
    fullExperiment.value = fe;
    const appInterfaceId = (fe as any).experiment?.execution_id;
    if (appInterfaceId) {
      try {
        const iface = (await services.ApplicationInterfaceService.retrieve(
          { lookup: appInterfaceId },
          { ignoreErrors: true },
        )) as ApplicationInterface;
        applicationInterface.value = iface;
      } catch (error) {
        if (!errors.ErrorUtils.isNotFoundError(error)) {
          errors.UnhandledErrorDispatcher.reportUnhandledError(error);
        }
      }
    }
    await loadGroupResourceProfile();
    initPollingExperiment();
  }

  function setLaunching({ launching: l }: { launching: boolean }): void {
    launching.value = l;
    if (l) {
      initPollingExperiment();
    }
  }

  async function loadExperiment({
    experimentId: id,
    showSpinner = false,
  }: {
    experimentId: string;
    showSpinner?: boolean;
  }): Promise<void> {
    const fe = (await services.FullExperimentService.retrieve(
      { lookup: id },
      { ignoreErrors: true, showSpinner },
    )) as FullExperiment;
    fullExperiment.value = fe;
  }

  async function pollExperiment(): Promise<void> {
    if (!fullExperiment.value) {
      polling.value = false;
      return;
    }
    const fe = fullExperiment.value as any;
    if (
      (launching.value && !fe.experiment?.hasLaunched) ||
      fe.experiment?.isProgressing
    ) {
      try {
        await loadExperiment({ experimentId: fe.experiment_id });
        setTimeout(() => void pollExperiment(), 3000);
      } catch {
        setTimeout(() => void pollExperiment(), 30000);
      }
    } else {
      polling.value = false;
    }
  }

  function initPollingExperiment(): void {
    if (!isPolling.value) {
      polling.value = true;
      void pollExperiment();
    }
  }

  async function clone(): Promise<void> {
    if (!experimentId.value) return;
    const cloned = (await services.ExperimentService.clone({
      lookup: experimentId.value,
    })) as Record<string, unknown>;
    clonedExperiment.value = cloned;
  }

  async function launch(): Promise<void> {
    if (!experimentId.value) return;
    try {
      await services.ExperimentService.launch({ lookup: experimentId.value });
      setLaunching({ launching: true });
    } catch {
      // TODO: handle launch error
    }
  }

  async function cancel(): Promise<void> {
    if (!experimentId.value) return;
    await services.ExperimentService.cancel({ lookup: experimentId.value });
    await loadExperiment({ experimentId: experimentId.value });
  }

  async function submitFetchIntermediateOutputs({
    outputNames,
  }: {
    outputNames: string[];
  }): Promise<void> {
    if (!experimentId.value) return;
    await services.ExperimentService.fetchIntermediateOutputs({
      lookup: experimentId.value,
      data: { outputNames },
    });
    const updated: RunningIntermediateOutputFetches = {
      ...runningIntermediateOutputFetches.value,
    };
    for (const name of outputNames) {
      updated[name] = new Date();
    }
    runningIntermediateOutputFetches.value = updated;
  }

  async function loadGroupResourceProfile(): Promise<void> {
    if (!groupResourceProfileId.value) return;
    const grp = (await services.ProjectResourceProfileService.retrieve({
      lookup: groupResourceProfileId.value,
    })) as GroupResourceProfile;
    groupResourceProfile.value = grp;
  }

  // ---------------------------------------------------------------------------
  // Expose
  // ---------------------------------------------------------------------------
  return {
    // state
    fullExperiment,
    launching,
    polling,
    clonedExperiment,
    runningIntermediateOutputFetches,
    applicationInterface,
    groupResourceProfile,
    // getters
    isPolling,
    experimentId,
    experiment,
    isExecuting,
    isFinished,
    finishedOrExecuting,
    outputDataProducts,
    currentlyRunningIntermediateOutputFetches,
    userHasWriteAccess,
    isJobActive,
    showQueueSettings,
    groupResourceProfileId,
    // actions
    setInitialFullExperimentData,
    setFullExperiment,
    setLaunching,
    loadExperiment,
    pollExperiment,
    initPollingExperiment,
    clone,
    launch,
    cancel,
    submitFetchIntermediateOutputs,
    loadGroupResourceProfile,
  };
});
