<template>
  <div>
    <div class="row">
      <div class="col">
        <h1 class="h4 mb-4">Experiment Statistics</h1>
      </div>
    </div>
    <div class="card" header="Load experiment details" no-body>
      <ul class="nav nav-tabs" card>
        <li class="nav-item" title="By Experiment ID" active>
          <div class="card-text">
            <div class="mb-3">
              <div class="input-group">
                <input
                  v-model.trim="experimentId"
                  class="form-control"
                  placeholder="Experiment ID"
                  @keydown.enter="experimentId && showExperimentDetails(experimentId!)"
                />
                <span class="input-group-text">
                  <button
                    class="btn"
                    :disabled="!experimentId"
                    @click="experimentId && showExperimentDetails(experimentId!)"
                  >
                    Load
                  </button>
                </span>
              </div>
            </div>
          </div>
        </li>
        <li class="nav-item" title="By Job ID">
          <div class="card-text">
            <div class="mb-3">
              <div class="input-group">
                <input
                  v-model.trim="jobId"
                  class="form-control"
                  placeholder="Job ID"
                  @keydown.enter="jobId && showExperimentDetailsForJobId(jobId!)"
                />
                <span class="input-group-text">
                  <button
                    class="btn"
                    :disabled="!jobId"
                    @click="jobId && showExperimentDetailsForJobId(jobId!)"
                  >
                    Load
                  </button>
                </span>
              </div>
            </div>
          </div>
        </li>
      </ul>
    </div>
    <div class="card" no-body>
      <ul ref="tabs" class="nav nav-tabs">
        <li class="nav-item" :title="selectedExperimentsTabTitle">
          <div class="row">
            <div class="col">
              <div class="card" header="Filter Options">
                <div class="input-group w-100 mb-2">
                  <span class="input-group-text">
                    <i class="fa fa-calendar-week" aria-hidden="true"></i>
                  </span>
                  <flat-pickr
                    :value="dateRange"
                    :config="dateConfig"
                    class="form-control"
                    @on-change="dateRangeChanged"
                  />
                  <span class="input-group-text">
                    <button class="btn" @click="getPast24Hours">Past 24 Hours</button>
                    <button class="btn" @click="getPastWeek">Past Week</button>
                  </span>
                </div>
                <div class="dropdown mb-2">
                  <a
                    v-if="!usernameFilterEnabled"
                    class="dropdown-item"
                    @click="usernameFilterEnabled = true"
                    >Username</a
                  >
                  <a
                    v-if="!applicationNameFilterEnabled"
                    class="dropdown-item"
                    @click="applicationNameFilterEnabled = true"
                    >Application Name</a
                  >
                  <a
                    v-if="!hostnameFilterEnabled"
                    class="dropdown-item"
                    @click="hostnameFilterEnabled = true"
                    >Hostname</a
                  >
                </div>
                <div v-if="usernameFilterEnabled" class="input-group mb-2">
                  <input
                    v-model="usernameFilter"
                    class="form-control"
                    placeholder="Username"
                    @keydown.enter="loadStatistics"
                  />
                  <span class="input-group-text">
                    <button class="btn" @click="removeUsernameFilter">
                      <i class="fa fa-times"></i>
                      <span class="visually-hidden">Remove username filter</span>
                    </button>
                  </span>
                </div>
                <div v-if="applicationNameFilterEnabled" class="input-group mb-2">
                  <select
                    v-model="applicationNameFilter"
                    class="form-select"
                    :options="applicationNameOptions"
                    @input="loadStatistics"
                  >
                    <option :value="null" disabled>Select an application to filter on</option>
                  </select>
                  <span class="input-group-text">
                    <button class="btn" @click="removeApplicationNameFilter">
                      <i class="fa fa-times"></i>
                      <span class="visually-hidden">Remove application name filter</span>
                    </button>
                  </span>
                </div>
                <div v-if="hostnameFilterEnabled" class="input-group mb-2">
                  <select
                    v-model="hostnameFilter"
                    class="form-select"
                    :options="hostnameOptions"
                    @input="loadStatistics"
                  >
                    <option :value="null" disabled>Select compute resource to filter on</option>
                  </select>
                  <span class="input-group-text">
                    <button class="btn" @click="removeHostnameFilter">
                      <i class="fa fa-times"></i>
                      <span class="visually-hidden">Remove hostname filter</span>
                    </button>
                  </span>
                </div>
                <div class="d-flex justify-content-end">
                  <button class="btn ms-auto" @click="loadStatistics">Get Statistics</button>
                </div>
              </div>
            </div>
          </div>
          <div class="row">
            <div class="col">
              <h2 class="h5 mb-4">
                Experiment Statistics from {{ fromTimeDisplay }} to
                {{ toTimeDisplay }}
              </h2>
            </div>
          </div>
          <div class="row">
            <div class="col-xl-2 col-md-4">
              <experiment-statistics-card
                bg-variant="primary"
                header-text-variant="white"
                :count="experimentStatistics.allExperimentCount || 0"
                title="Total Experiments"
                @click="selectExperiments('allExperiments')"
              >
                <template #link-text>
                  <span>All</span>
                </template>
              </experiment-statistics-card>
            </div>
            <div class="col-xl-2 col-md-4">
              <experiment-statistics-card
                bg-variant="light"
                :count="experimentStatistics.createdExperimentCount || 0"
                :states="createdStates"
                title="Created Experiments"
                @click="selectExperiments('createdExperiments')"
              >
              </experiment-statistics-card>
            </div>
            <div class="col-xl-2 col-md-4">
              <experiment-statistics-card
                bg-variant="light"
                header-text-variant="success"
                :count="experimentStatistics.runningExperimentCount || 0"
                :states="runningStates"
                title="Running Experiments"
                @click="selectExperiments('runningExperiments')"
              >
              </experiment-statistics-card>
            </div>
            <div class="col-xl-2 col-md-4">
              <experiment-statistics-card
                bg-variant="success"
                header-text-variant="white"
                link-variant="success"
                :count="experimentStatistics.completedExperimentCount || 0"
                :states="completedStates"
                title="Completed Experiments"
                @click="selectExperiments('completedExperiments')"
              >
              </experiment-statistics-card>
            </div>
            <div class="col-xl-2 col-md-4">
              <experiment-statistics-card
                bg-variant="warning"
                header-text-variant="white"
                link-variant="warning"
                :count="experimentStatistics.cancelledExperimentCount || 0"
                :states="canceledStates"
                title="Cancelled Experiments"
                @click="selectExperiments('cancelledExperiments')"
              >
              </experiment-statistics-card>
            </div>
            <div class="col-xl-2 col-md-4">
              <experiment-statistics-card
                bg-variant="danger"
                header-text-variant="white"
                link-variant="danger"
                :count="experimentStatistics.failedExperimentCount || 0"
                :states="failedStates"
                title="Failed Experiments"
                @click="selectExperiments('failedExperiments')"
              >
              </experiment-statistics-card>
            </div>
          </div>
          <div v-if="items.length > 0" class="row">
            <div class="col">
              <div class="card">
                <div class="card-body">
                  <!-- TODO: Replace b-table with native table -->
                  <table class="table">
                    <tbody>
                      <tr v-for="item in items" :key="item.experiment_id">
                        <td><application-name :application-interface-id="item.execution_id" /></td>
                        <td>
                          <compute-resource-name :compute-resource-id="item.resource_host_id" />
                        </td>
                        <td><human-date :date="item.creation_time" /></td>
                        <td>
                          <experiment-status-badge :status-name="item.experiment_status.name" />
                        </td>
                        <td>
                          <a @click="showExperimentDetails(item.experiment_id)">
                            View Details
                            <i class="far fa-chart-bar" aria-hidden="true"></i>
                          </a>
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
              <pager
                v-if="experimentStatistics.allExperimentCount && experimentStatistics.allExperimentCount > 0"
                :paginator="experimentStatisticsPaginator"
                @next="experimentStatisticsPaginator?.next()"
                @previous="experimentStatisticsPaginator?.previous()"
              ></pager>
            </div>
          </div>
        </li>
        <li
          v-for="experimentTab in experimentDetailTabs"
          :key="experimentTab.experiment.experiment_id"
          class="nav-item"
        >
          <span class="nav-link">
            {{ experimentTab.tabTitle }}
            <a
              class="text-secondary"
              @click="removeExperimentDetailTab(experimentTab.experiment.experiment_id)"
            >
              <i class="fas fa-times"></i>
              <span class="visually-hidden">Close experiment tab</span>
            </a>
          </span>
          <experiment-details-view :experiment="experimentTab.experiment" />
        </li>
      </ul>
    </div>
  </div>
</template>
<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { errors, models, services, utils } from "django-airavata-api";
import { notifications } from "django-airavata-common-ui";
import { formatDate, formatIsoDate } from "django-airavata-common-ui/js/utils/dates.js";
import ExperimentStatisticsCard from "./ExperimentStatisticsCard.vue";
import ExperimentDetailsView from "./ExperimentDetailsView.vue";

// fp_incr sets the time of the date to midnight.
// Calculating from today midnight to tomorrow midnight.
const _fromTime = (new Date() as unknown as { fp_incr: (_n: number) => Date }).fp_incr(0);
const _toTime = (new Date() as unknown as { fp_incr: (_n: number) => Date }).fp_incr(1);

type ExperimentSummary = {
  experiment_id: string;
  execution_id: string;
  resource_host_id: string;
  creation_time: Date | string;
  experiment_status: { name: string };
  [key: string]: unknown;
};
type ExperimentStatisticsResults = {
  allExperimentCount?: number;
  createdExperimentCount?: number;
  runningExperimentCount?: number;
  completedExperimentCount?: number;
  cancelledExperimentCount?: number;
  failedExperimentCount?: number;
  allExperiments?: ExperimentSummary[];
  createdExperiments?: ExperimentSummary[];
  runningExperiments?: ExperimentSummary[];
  completedExperiments?: ExperimentSummary[];
  cancelledExperiments?: ExperimentSummary[];
  failedExperiments?: ExperimentSummary[];
  [key: string]: unknown;
};
const experimentStatisticsPaginator = ref<{
  results: ExperimentStatisticsResults;
  offset: number;
  next: () => void;
  previous: () => void;
} | null>(null);
const selectedExperimentSummariesKey = ref<string | null>(null);
const fromTime = ref<Date>(_fromTime);
const toTime = ref<Date>(_toTime);
const dateRange = ref<(Date | string)[]>([_fromTime, _toTime]);
const dateConfig = ref({
  mode: "range",
  wrap: true,
  dateFormat: "Y-m-d",
  maxDate: (new Date() as unknown as { fp_incr: (_n: number) => Date }).fp_incr(1),
});
const usernameFilterEnabled = ref(false);
const usernameFilter = ref<string | null>(null);
const applicationNameFilterEnabled = ref(false);
const applicationNameFilter = ref<string | null>(null);
const hostnameFilterEnabled = ref(false);
const hostnameFilter = ref<string | null>(null);
const appInterfaces = ref<{ application_interface_id: string; application_name: string }[] | null>(null);
const computeResourceNames = ref<{ host_id: string; host: string }[] | null>(null);
const experimentDetailTabs = ref<{ tabTitle: string; experiment: { experiment_id: string; experiment_name: string } }[]>([]);
const experimentId = ref<string | null>(null);
const jobId = ref<string | null>(null);
const activeTabIndex = ref(0);
const tabs = ref<HTMLElement | null>(null);

const experimentStatistics = computed<ExperimentStatisticsResults>(() =>
  experimentStatisticsPaginator.value ? experimentStatisticsPaginator.value.results : {}
);

const createdStates = computed(() => [models.ExperimentState.CREATED, models.ExperimentState.VALIDATED]);
const runningStates = computed(() => [
  models.ExperimentState.SCHEDULED,
  models.ExperimentState.LAUNCHED,
  models.ExperimentState.EXECUTING,
]);
const completedStates = computed(() => [models.ExperimentState.COMPLETED]);
const canceledStates = computed(() => [models.ExperimentState.CANCELING, models.ExperimentState.CANCELED]);
const failedStates = computed(() => [models.ExperimentState.FAILED]);

const fromTimeDisplay = computed(() => formatDate(fromTime.value));
const toTimeDisplay = computed(() => formatDate(toTime.value));

const selectedExperimentSummaries = computed<ExperimentSummary[]>(() => {
  if (
    selectedExperimentSummariesKey.value &&
    experimentStatistics.value &&
    selectedExperimentSummariesKey.value in experimentStatistics.value
  ) {
    return (experimentStatistics.value[selectedExperimentSummariesKey.value] as ExperimentSummary[]) ?? [];
  }
  return [];
});

const items = computed(() => selectedExperimentSummaries.value ?? []);

const applicationNameOptions = computed(() => {
  if (appInterfaces.value) {
    const options = appInterfaces.value.map((appInterface) => ({
      value: appInterface.application_interface_id,
      text: appInterface.application_name,
    }));
    return utils.StringUtils.sortIgnoreCase(options, (o: { text: string }) => o.text);
  }
  return [];
});

const hostnameOptions = computed(() => {
  if (!computeResourceNames.value) return [];
  const options = computeResourceNames.value.map((name) => ({
    value: name.host_id,
    text: name.host,
  }));
  return utils.StringUtils.sortIgnoreCase(options, (o: { text: string }) => o.text);
});

const selectedExperimentsTabTitle = computed(() => {
  const map: Record<string, string> = {
    allExperiments: "All Experiments",
    createdExperiments: "Created Experiments",
    runningExperiments: "Running Experiments",
    completedExperiments: "Completed Experiments",
    cancelledExperiments: "Cancelled Experiments",
    failedExperiments: "Failed Experiments",
  };
  return selectedExperimentSummariesKey.value
    ? (map[selectedExperimentSummariesKey.value] ?? "Experiments")
    : "Experiments";
});

function dateRangeChanged(selectedDates: Date[]) {
  [fromTime.value, toTime.value] = selectedDates;
  if (fromTime.value && toTime.value) {
    loadStatistics();
  }
}

function loadApplicationInterfaces() {
  return services.ApplicationInterfaceService.list().then(
    (appIfaces: typeof appInterfaces.value) => (appInterfaces.value = appIfaces)
  );
}

function loadComputeResources() {
  return services.ComputeResourceService.namesList().then(
    (names: typeof computeResourceNames.value) => (computeResourceNames.value = names)
  );
}

function loadStatistics() {
  const requestData: Record<string, string> = {
    fromTime: fromTime.value.toJSON(),
    toTime: toTime.value.toJSON(),
  };
  if (usernameFilterEnabled.value && usernameFilter.value) {
    requestData["user_name"] = usernameFilter.value;
  }
  if (applicationNameFilterEnabled.value && applicationNameFilter.value) {
    requestData["application_name"] = applicationNameFilter.value;
  }
  if (hostnameFilterEnabled.value && hostnameFilter.value) {
    requestData["resource_host_name"] = hostnameFilter.value;
  }
  return services.ExperimentStatisticsService.get(requestData).then((stats: typeof experimentStatisticsPaginator.value) => {
    experimentStatisticsPaginator.value = stats;
  });
}

function getPast24Hours() {
  fromTime.value = (new Date() as unknown as { fp_incr: (_n: number) => Date }).fp_incr(0);
  toTime.value = (new Date() as unknown as { fp_incr: (_n: number) => Date }).fp_incr(1);
  updateDateRange();
}

function getPastWeek() {
  fromTime.value = (new Date() as unknown as { fp_incr: (_n: number) => Date }).fp_incr(-7);
  toTime.value = (new Date() as unknown as { fp_incr: (_n: number) => Date }).fp_incr(1);
  updateDateRange();
}

function updateDateRange() {
  dateRange.value = [formatIsoDate(fromTime.value), formatIsoDate(toTime.value)];
}

function removeUsernameFilter() {
  usernameFilter.value = null;
  usernameFilterEnabled.value = false;
  loadStatistics();
}

function removeApplicationNameFilter() {
  applicationNameFilter.value = null;
  applicationNameFilterEnabled.value = false;
  loadStatistics();
}

function removeHostnameFilter() {
  hostnameFilter.value = null;
  hostnameFilterEnabled.value = false;
  loadStatistics();
}

async function showExperimentDetails(expId: string, tabTitle: string | null = null) {
  const expDetailsIndex = getExperimentDetailTabsIndex(expId);
  if (expDetailsIndex >= 0) {
    if (tabTitle) {
      experimentDetailTabs.value[expDetailsIndex].tabTitle = tabTitle;
    }
    selectExperimentDetailsTab(expId);
  } else {
    try {
      const exp = await services.ExperimentService.retrieve(
        { lookup: expId },
        { ignoreErrors: true }
      );
      experimentDetailTabs.value.push({
        tabTitle: tabTitle || exp.experiment_name,
        experiment: exp,
      });
      selectExperimentDetailsTab(expId);
      scrollTabsIntoView();
    } catch (error) {
      if (errors.ErrorUtils.isNotFoundError(error)) {
        notifications.NotificationList.add(
          new notifications.Notification({
            type: "WARNING",
            message: `No experiment exists with experiment id ${expId}`,
            duration: 5,
          })
        );
      } else {
        utils.FetchUtils.reportError(error);
      }
    }
  }
}

async function showExperimentDetailsForJobId(jId: string) {
  const searchResults = await services.ExperimentSearchService.list({
    [models.ExperimentSearchFields.JOB_ID.name]: jId,
  });
  if (searchResults.results.length === 0) {
    notifications.NotificationList.add(
      new notifications.Notification({
        type: "WARNING",
        message: `No experiment exists with job id ${jId}`,
        duration: 5,
      })
    );
  } else {
    if (searchResults.results.length > 1) {
      notifications.NotificationList.add(
        new notifications.Notification({
          type: "WARNING",
          message: `More than one experiment matches job id ${jId}, showing the latest one`,
          duration: 5,
        })
      );
    }
    showExperimentDetails(searchResults.results[0].experiment_id, `Job ${jId}`);
  }
}

function selectExperimentDetailsTab(expId: string) {
  const expDetailsIndex = getExperimentDetailTabsIndex(expId);
  // Note: running this in nextTick doesn't work, but setTimeout does
  setTimeout(() => {
    activeTabIndex.value = expDetailsIndex + 1;
  }, 1);
}

function getExperimentDetailTabsIndex(expId: string) {
  return experimentDetailTabs.value.findIndex(
    (tab) => tab.experiment.experiment_id === expId
  );
}

function removeExperimentDetailTab(expId: string) {
  const index = getExperimentDetailTabsIndex(expId);
  experimentDetailTabs.value.splice(index, 1);
}

function scrollTabsIntoView() {
  tabs.value?.scrollIntoView({ behavior: "smooth" });
}

function selectExperiments(experimentSummariesKey: string) {
  if (experimentStatisticsPaginator.value && experimentStatisticsPaginator.value.offset > 0) {
    loadStatistics();
  }
  selectedExperimentSummariesKey.value = experimentSummariesKey;
}

onMounted(() => {
  loadStatistics();
  loadApplicationInterfaces();
  loadComputeResources();
});
</script>
