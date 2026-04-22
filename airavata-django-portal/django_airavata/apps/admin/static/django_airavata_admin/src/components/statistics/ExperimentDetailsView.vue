<template>
  <div>
    <table v-if="fullExperiment" class="table">
      <tbody>
        <tr>
          <th scope="row">Name</th>
          <td>
            <div :title="experiment.experiment_id">
              {{ experiment.experiment_name }}
            </div>
            <small class="text-muted">
              ID: {{ experiment.experiment_id }} (<clipboard-copy-link
                :text="experiment.experiment_id"
                :link-classes="['text-reset']"
              >
                copy
                <template #icon>
                  <span></span>
                </template>
                <template #tooltip>
                  <span>Copied ID!</span>
                </template> </clipboard-copy-link
              >)
            </small>
          </td>
        </tr>
        <tr>
          <th scope="row">Description</th>
          <td>{{ experiment.description }}</td>
        </tr>
        <tr>
          <th scope="row">Project</th>
          <td v-if="fullExperiment.project">
            {{ fullExperiment.projectName }}
          </td>
          <td v-else>
            <em>You don't have access to this project.</em>
          </td>
        </tr>
        <tr>
          <th scope="row">Owner</th>
          <td>{{ experiment.user_name }}</td>
        </tr>
        <tr>
          <th scope="row">Application</th>
          <td v-if="fullExperiment.application_name">
            {{ fullExperiment.application_name }}
          </td>
          <td v-else class="font-italic text-muted">
            Unable to load interface {{ fullExperiment.experiment.execution_id }}
          </td>
        </tr>
        <tr>
          <th scope="row">Compute Resource</th>
          <td v-if="fullExperiment.computeHostName">
            {{ fullExperiment.computeHostName }}
          </td>
          <td v-else class="font-italic text-muted">
            Unable to load compute resource {{ fullExperiment.resource_host_id }}
          </td>
        </tr>
        <tr>
          <th scope="row">Experiment Status</th>
          <td>
            <template v-if="fullExperiment.experiment.isProgressing">
              <i class="fa fa-sync-alt fa-spin"></i>
              <span class="visually-hidden">Progressing...</span>
            </template>
            {{ fullExperiment.experimentStatusName }}
          </td>
        </tr>
        <tr v-if="fullExperiment.jobDetails && fullExperiment.jobDetails.length > 0">
          <th scope="row">Job</th>
          <td>
            <table class="table">
              <thead>
                <th>Name</th>
                <th>ID</th>
                <th>Status</th>
                <th>Creation Time</th>
              </thead>
              <tbody>
                <tr v-for="(jobDetail, index) in fullExperiment.jobDetails" :key="jobDetail.jobId">
                  <td>{{ jobDetail.jobName }}</td>
                  <td>{{ jobDetail.jobId }}</td>
                  <td>{{ jobDetail.jobStatusStateName }}</td>
                  <td>
                    <span :title="jobDetail.creation_time.toString()">{{
                      jobCreationTimes[index]
                    }}</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </td>
        </tr>
        <tr>
          <th scope="row">Notification List</th>
          <td>
            {{ experiment.emailAddresses ? experiment.emailAddresses.join(", ") : "" }}
          </td>
        </tr>
        <tr v-if="fullExperiment.jobDetails && fullExperiment.jobDetails.length > 0">
          <th scope="row">Working Dir</th>
          <td>
            <div v-for="jobDetail in fullExperiment.jobDetails" :key="jobDetail.jobId">
              {{ jobDetail.jobName }}: {{ jobDetail.workingDir }}
            </div>
          </td>
        </tr>
        <tr v-if="fullExperiment.jobDetails && fullExperiment.jobDetails.length > 0">
          <th scope="row">Job Description</th>
          <td>
            <div
              v-for="jobDetail in fullExperiment.jobDetails"
              :key="jobDetail.jobId"
              class="card"
              :header="jobDetail.jobName"
            >
              <pre>{{ jobDetail.jobDescription }}</pre>
            </div>
          </td>
        </tr>
        <tr>
          <th scope="row">Creation Time</th>
          <td>
            <span :title="experiment.creation_time.toString()">{{ creationTime }}</span>
          </td>
        </tr>
        <tr>
          <th scope="row">Last Modified Time</th>
          <td>
            <span :title="fullExperiment.experimentStatus.time_of_state_change.toString()">{{
              lastModifiedTime
            }}</span>
          </td>
        </tr>
        <tr>
          <th scope="row">Wall Time Limit</th>
          <td>
            {{ experiment.userConfigurationData.computationalResourceScheduling.wallTimeLimit }}
            minutes
          </td>
        </tr>
        <tr>
          <th scope="row">CPU Count</th>
          <td>
            {{ experiment.userConfigurationData.computationalResourceScheduling.totalCPUCount }}
          </td>
        </tr>
        <tr>
          <th scope="row">Node Count</th>
          <td>
            {{ experiment.userConfigurationData.computationalResourceScheduling.nodeCount }}
          </td>
        </tr>
        <tr
          v-if="
            experiment.userConfigurationData.computationalResourceScheduling.totalPhysicalMemory
          "
        >
          <th scope="row">Total Physical Memory</th>
          <td>
            {{
              experiment.userConfigurationData.computationalResourceScheduling.totalPhysicalMemory.toLocaleString()
            }}
            MB
          </td>
        </tr>
        <tr>
          <th scope="row">Queue</th>
          <td>
            {{ experiment.userConfigurationData.computationalResourceScheduling.queueName }}
          </td>
        </tr>
        <tr>
          <th scope="row">Inputs</th>
          <td>
            <ul>
              <li v-for="input in experiment.experimentInputs" :key="input.name">
                {{ input.name }}:
                <template v-if="input.type.isSimpleValueType">
                  <span class="text-break">{{ input.value }}</span>
                </template>
                <data-product-viewer
                  v-for="dp in inputDataProducts[input.name]"
                  v-else-if="input.type.isFileValueType"
                  :key="dp.productUri"
                  :data-product="dp"
                  :input-file="true"
                />
              </li>
            </ul>
          </td>
        </tr>
        <tr>
          <th scope="row">Outputs</th>
          <td>
            <ul>
              <li v-for="output in experiment.experimentOutputs" :key="output.name">
                {{ output.name }}:
                <template v-if="output.type.isSimpleValueType">
                  <span class="text-break">{{ output.value }}</span>
                </template>
                <data-product-viewer
                  v-for="dp in outputDataProducts[output.name]"
                  v-else-if="output.type.isFileValueType"
                  :key="dp.productUri"
                  :data-product="dp"
                />
              </li>
            </ul>
          </td>
        </tr>
        <tr>
          <th scope="row">Experiment Data Dir</th>
          <td>
            <div>{{ experimentDataDir }}</div>
            <div v-if="archived" class="alert alert-warning mt-2">
              This directory was archived in
              <b>{{ experimentArchive?.archive_name }}</b> on {{ experimentArchive?.created_date }}.
            </div>
          </td>
        </tr>
        <tr>
          <th scope="row">Errors</th>
          <td>
            <div
              v-for="error in experiment.errors"
              :key="error.errorId"
              class="card"
              header="Error"
            >
              <p>{{ error.userFriendlyMessage }}</p>
              <pre class="pre-scrollable">{{ error.actualErrorMessage }}</pre>
            </div>
          </td>
        </tr>
        <template v-if="failedJobs.length > 0">
          <tr v-for="job in failedJobs" :key="job.jobId">
            <th scope="row">Job Submission Response</th>
            <td>
              <div v-if="job.stdOut" class="card" :header="job.jobName + ' STDOUT'">
                <pre class="pre-scrollable">{{ job.stdOut }}</pre>
              </div>
              <div v-if="job.stdErr" class="card" :header="job.jobName + ' STDERR'">
                <pre class="pre-scrollable">{{ job.stdErr }}</pre>
              </div>
            </td>
          </tr>
        </template>
      </tbody>
    </table>
    <h2 class="h5 mb-3">Process Details</h2>
    <div
      v-for="process in experiment.processes"
      :key="process.process_id"
      class="card"
      :header="process.process_id"
    >
      <div
        v-for="task in process.sortedTasks"
        :key="task.taskId"
        class="card"
        :header="task.taskId"
      >
        <table class="table table-sm">
          <tbody>
            <tr>
              <th scope="row">Task Id</th>
              <td>{{ task.taskId }}</td>
            </tr>
            <tr>
              <th scope="row">Task Type</th>
              <td>{{ task.taskType.name }}</td>
            </tr>
            <tr>
              <th scope="row">Task Status</th>
              <td>{{ task.latestStatus.state.name }}</td>
            </tr>
            <tr>
              <th scope="row">Task Status Time</th>
              <td>
                <human-date :date="task.latestStatus.timeOfStateChange" />
              </td>
            </tr>
            <tr>
              <th scope="row">Task Status Reason</th>
              <td>{{ task.latestStatus.reason }}</td>
            </tr>
            <template v-if="task.taskErrors && task.taskErrors.length > 0">
              <tr>
                <th scope="row">Task Errors</th>
                <td>
                  <div
                    v-for="error in task.taskErrors"
                    :key="error.errorId"
                    class="card"
                    :header="error.errorId"
                  >
                    <p>{{ error.userFriendlyMessage }}</p>
                    <pre class="pre-scrollable">{{ error.actualErrorMessage }}</pre>
                  </div>
                </td>
              </tr>
            </template>
            <template v-if="task.jobs && task.jobs.length > 0">
              <tr>
                <th scope="row">Jobs</th>
                <td>
                  <div v-for="job in task.jobs" :key="job.jobId" class="card" :header="job.jobName">
                    <pre>{{ job.jobDescription }}</pre>
                  </div>
                </td>
              </tr>
            </template>
          </tbody>
        </table>
      </div>

      <div
        v-for="error in process.processErrors"
        :key="error.errorId"
        class="card"
        :header="'Process Error ' + error.errorId"
      >
        <p>{{ error.userFriendlyMessage }}</p>
        <pre class="pre-scrollable">{{ error.actualErrorMessage }}</pre>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { models, services } from "django-airavata-api";
import { relativeTime } from "django-airavata-common-ui/js/utils/dates.js";

type DataProduct = { productUri: string; [key: string]: unknown };
type ExperimentIO = { name: string; value?: string; type?: { isSimpleValueType?: boolean; isFileValueType?: boolean; [key: string]: unknown } | unknown };
type JobDetail = { jobId: string; jobName?: string; workingDir?: string; jobDescription?: string; creation_time: Date | string | number; jobStatusStateName?: string; latestJobStatus?: { jobState: unknown }; stdOut?: string; stdErr?: string };
type FullExperimentInner = {
  experiment: { experimentInputs: ExperimentIO[]; experimentOutputs: ExperimentIO[]; execution_id?: string; isProgressing?: boolean; creation_time?: Date | string | number; [key: string]: unknown };
  inputDataProducts?: DataProduct[];
  outputDataProducts?: DataProduct[];
  project?: unknown;
  projectName?: string;
  application_name?: string;
  computeHostName?: string;
  experimentStatusName?: string;
  experimentStatus: { time_of_state_change: Date | string | number };
  jobDetails?: JobDetail[];
  [key: string]: unknown;
};
type ExperimentArchive = { archived?: boolean; archive_name?: string; created_date?: string };

const props = defineProps<{
  experiment: InstanceType<typeof models.Experiment>;
}>();

const fullExperiment = ref<FullExperimentInner | null>(null);
const experimentArchive = ref<ExperimentArchive | null>(null);

const inputDataProducts = computed(() => {
  const result: Record<string, DataProduct[]> = {};
  if (fullExperiment.value && fullExperiment.value.inputDataProducts) {
    fullExperiment.value.experiment.experimentInputs.forEach((input) => {
      result[input.name] = getDataProducts(input, fullExperiment.value!.inputDataProducts ?? []);
    });
  }
  return result;
});

const outputDataProducts = computed(() => {
  const result: Record<string, DataProduct[]> = {};
  if (fullExperiment.value && fullExperiment.value.outputDataProducts) {
    fullExperiment.value.experiment.experimentOutputs.forEach((output) => {
      result[output.name] = getDataProducts(output, fullExperiment.value!.outputDataProducts ?? []);
    });
  }
  return result;
});

const creationTime = computed(() =>
  fullExperiment.value?.experiment.creation_time
    ? relativeTime(fullExperiment.value.experiment.creation_time as Date | string | number)
    : ""
);

const lastModifiedTime = computed(() =>
  fullExperiment.value
    ? relativeTime(fullExperiment.value.experimentStatus.time_of_state_change)
    : ""
);

const jobCreationTimes = computed(() =>
  fullExperiment.value?.jobDetails
    ? fullExperiment.value.jobDetails.map((jobDetail) =>
        relativeTime(jobDetail.creation_time as Date | string | number)
      )
    : []
);

const failedJobs = computed(() => {
  if (fullExperiment.value?.jobDetails) {
    return fullExperiment.value.jobDetails.filter(
      (job) =>
        props.experiment.latestStatus.state === models.ExperimentState.FAILED ||
        (job.latestJobStatus && job.latestJobStatus.jobState === models.JobState.FAILED)
    );
  }
  return [];
});

const experimentDataDir = computed(() => {
  if (props.experiment?.userConfigurationData) {
    return props.experiment.userConfigurationData.experimentDataDir;
  }
  return null;
});

const archived = computed(() => experimentArchive.value?.archived);

function getDataProducts(io: ExperimentIO, collection: DataProduct[]): DataProduct[] {
  if (!io.value || !collection) {
    return [];
  }
  let dataProducts: (DataProduct | undefined)[] | null = null;
  if (io.type === models.DataType.URI_COLLECTION) {
    const dataProductURIs = io.value.split(",");
    dataProducts = dataProductURIs.map((uri) => collection.find((dp) => dp.productUri === uri));
  } else {
    const dataProductURI = io.value;
    dataProducts = collection.filter((dp) => dp.productUri === dataProductURI);
  }
  return dataProducts ? dataProducts.filter((dp): dp is DataProduct => !!dp) : [];
}

onMounted(() => {
  services.FullExperimentService.retrieve({
    lookup: props.experiment.experiment_id,
  }).then((fe: typeof fullExperiment.value) => (fullExperiment.value = fe));
  services.ExperimentArchiveService.get({
    experimentId: props.experiment.experiment_id,
  }).then((result: ExperimentArchive) => {
    experimentArchive.value = result;
  });
});
</script>

<style scoped>
.table {
  table-layout: fixed;
}
.table th[scope="row"] {
  width: 20%;
}
</style>
