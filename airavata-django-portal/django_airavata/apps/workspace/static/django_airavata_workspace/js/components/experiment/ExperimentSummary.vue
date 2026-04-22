<template>
  <div v-if="localFullExperiment">
    <div class="row">
      <div class="col-auto me-auto">
        <h1 class="h4 mb-4">
          <slot name="title">Experiment Summary</slot>
        </h1>
      </div>
      <div class="col-auto">
        <ShareButton :entity-id="localExperiment.experiment_id" />
        <a v-if="isEditable" class="btn btn-primary" :href="editLink">
          Edit
          <i class="fa fa-edit" aria-hidden="true"></i>
        </a>
        <a v-if="isLaunchable" class="btn btn-primary" @click="onLaunch">
          Launch
          <i class="fa fa-running" aria-hidden="true"></i>
        </a>
        <button v-if="isClonable" class="btn btn-primary" @click="onClone">
          Clone
          <i class="fa fa-copy" aria-hidden="true"></i>
        </button>
        <button v-if="isCancelable" class="btn btn-primary" @click="onCancel">
          Cancel
          <i class="fa fa-window-close" aria-hidden="true"></i>
        </button>
      </div>
    </div>
    <template v-for="output in localExperiment.experiment_outputs" :key="output.name">
      <div v-if="finishedOrExecuting" class="row">
        <div class="col">
          <OutputDisplayContainer :experiment-output="output" />
        </div>
      </div>
    </template>
    <div v-if="finishedOrExecuting" class="row">
      <div class="col">
        <ExperimentStorageViewContainer :experiment-id="localExperiment.experiment_id" />
      </div>
    </div>
    <div class="row">
      <div class="col">
        <div class="card border-default">
          <div class="card-body">
            <table class="table">
              <tbody>
                <tr>
                  <th scope="row">Name</th>
                  <td>
                    <div :title="localExperiment.experiment_id">
                      {{ localExperiment.experiment_name }}
                    </div>
                    <small class="text-muted">
                      ID: {{ localExperiment.experiment_id }} (<ClipboardCopyLink
                        :text="localExperiment.experiment_id"
                        :link-classes="['text-reset']"
                      >
                        copy
                        <template #icon>
                          <span></span>
                        </template>
                        <template #tooltip>
                          <span>Copied ID!</span>
                        </template> </ClipboardCopyLink
                      >)
                    </small>
                  </td>
                </tr>
                <tr>
                  <th scope="row">Description</th>
                  <td>{{ localExperiment.description }}</td>
                </tr>
                <tr>
                  <th scope="row">Project</th>
                  <td v-if="localFullExperiment.project">
                    {{ localFullExperiment.projectName }}
                  </td>
                  <td v-else>
                    <em>You don't have access to this project.</em>
                  </td>
                </tr>
                <tr>
                  <th scope="row">Owner</th>
                  <td>{{ localExperiment.user_name }}</td>
                </tr>
                <tr>
                  <th scope="row">Application</th>
                  <td v-if="localFullExperiment.applicationName">
                    {{ localFullExperiment.applicationName }}
                  </td>
                  <td v-else class="font-italic text-muted">
                    Unable to load interface
                    {{ localFullExperiment.experiment.execution_id }}
                  </td>
                </tr>
                <tr>
                  <th scope="row">Compute Resource</th>
                  <td v-if="localFullExperiment.computeHostName">
                    {{ localFullExperiment.computeHostName }}
                  </td>
                  <td v-else class="font-italic text-muted">
                    Unable to load compute resource
                    {{ localFullExperiment.resourceHostId }}
                  </td>
                </tr>
                <tr>
                  <th scope="row">Experiment Status</th>
                  <td>
                    <template v-if="localFullExperiment.experiment.isProgressing">
                      <i class="fa fa-sync-alt fa-spin"></i>
                      <span class="visually-hidden">Progressing...</span>
                    </template>
                    {{ localFullExperiment.experimentStatusName }}
                  </td>
                </tr>
                <tr
                  v-if="
                    localFullExperiment.job_details && localFullExperiment.job_details.length > 0
                  "
                >
                  <th scope="row">Job</th>
                  <td>
                    <table class="table">
                      <thead>
                        <th>Name</th>
                        <th>ID</th>
                        <th>Status</th>
                        <th>Creation Time</th>
                      </thead>
                      <tr
                        v-for="(jobDetail, index) in localFullExperiment.job_details"
                        :key="jobDetail.job_id"
                      >
                        <td>{{ jobDetail.job_name }}</td>
                        <td>{{ jobDetail.job_id }}</td>
                        <td>{{ jobDetail.jobStatusStateName }}</td>
                        <td>
                          <span :title="String(jobDetail.creation_time)">{{
                            jobCreationTimes[index]
                          }}</span>
                        </td>
                      </tr>
                    </table>
                  </td>
                </tr>
                <tr>
                  <th scope="row">Creation Time</th>
                  <td>
                    <span :title="String(localExperiment.creation_time)">{{ creationTime }}</span>
                  </td>
                </tr>
                <tr>
                  <th scope="row">Last Modified Time</th>
                  <td>
                    <span
                      :title="String(localFullExperiment.experimentStatus.time_of_state_change)"
                      >{{ lastModifiedTime }}</span
                    >
                  </td>
                </tr>
                <tr v-if="groupResourceProfile">
                  <th scope="row">Allocation</th>
                  <td>
                    <a :href="viewGroupResourceProfileLink ?? undefined">
                      {{ (groupResourceProfile as Record<string, unknown>).groupResourceProfileName }}
                    </a>
                  </td>
                </tr>
                <tr v-if="showQueueSettings">
                  <th scope="row">Wall Time Limit</th>
                  <td>
                    {{
                      localExperiment.user_configuration_data.computational_resource_scheduling
                        .wall_time_limit
                    }}
                    minutes
                  </td>
                </tr>
                <tr v-if="showQueueSettings">
                  <th scope="row">CPU Count</th>
                  <td>
                    {{
                      localExperiment.user_configuration_data.computational_resource_scheduling
                        .total_cpu_count
                    }}
                  </td>
                </tr>
                <tr v-if="showQueueSettings">
                  <th scope="row">Node Count</th>
                  <td>
                    {{
                      localExperiment.user_configuration_data.computational_resource_scheduling
                        .node_count
                    }}
                  </td>
                </tr>
                <tr
                  v-if="
                    showQueueSettings &&
                    localExperiment.user_configuration_data.computational_resource_scheduling
                      .total_physical_memory
                  "
                >
                  <th scope="row">Total Physical Memory</th>
                  <td>
                    {{
                      localExperiment.user_configuration_data.computational_resource_scheduling.total_physical_memory.toLocaleString()
                    }}
                    MB
                  </td>
                </tr>
                <tr v-if="showQueueSettings">
                  <th scope="row">Queue</th>
                  <td>
                    {{
                      localExperiment.user_configuration_data.computational_resource_scheduling
                        .queue_name
                    }}
                  </td>
                </tr>
                <tr>
                  <th scope="row">Inputs</th>
                  <td>
                    <ul>
                      <li v-for="input in localExperiment.experiment_inputs" :key="input.name">
                        {{ input.name }}:
                        <template v-if="input.type.isSimpleValueType">
                          <span class="text-break">{{ input.value }}</span>
                        </template>
                        <DataProductViewer
                          v-for="dp in inputDataProducts[input.name]"
                          v-else-if="input.type.isFileValueType"
                          :key="(dp as Record<string, unknown>).product_uri as string"
                          :data-product="dp as Record<string, unknown>"
                          :input-file="true"
                        />
                      </li>
                    </ul>
                  </td>
                </tr>
                <tr>
                  <th scope="row">Errors</th>
                  <td>
                    <div
                      v-for="error in localExperiment.errors"
                      :key="error.errorId"
                      class="card"
                      header="Error"
                    >
                      <p>{{ error.userFriendlyMessage }}</p>
                    </div>
                  </td>
                </tr>
                <template v-if="failedJobs.length > 0">
                  <tr v-for="job in failedJobs" :key="job.job_id">
                    <th scope="row">Job Submission Response</th>
                    <td>
                      <div v-if="job.std_out" class="card" :header="job.job_name + ' STDOUT'">
                        <pre class="pre-scrollable">{{ job.std_out }}</pre>
                      </div>
                      <div v-if="job.std_err" class="card" :header="job.job_name + ' STDERR'">
                        <pre class="pre-scrollable">{{ job.std_err }}</pre>
                      </div>
                    </td>
                  </tr>
                </template>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { models } from "django-airavata-api";
import { components, notifications } from "django-airavata-common-ui";
import OutputDisplayContainer from "./output-displays/OutputDisplayContainer.vue";
import urls from "../../utils/urls";
import { relativeTime } from "django-airavata-common-ui/js/utils/dates.js";
import ExperimentStorageViewContainer from "../storage/ExperimentStorageViewContainer.vue";
import DataProductViewer from "django-airavata-common-ui/js/components/DataProductViewer.vue";
import { useExperimentStore } from "django-airavata-common-ui/js/stores/experiment";

const ClipboardCopyLink = components.ClipboardCopyLink;
const ShareButton = components.ShareButton;

// Local interface to give the template enough type information for FullExperiment
interface JobDetail {
  job_id: string;
  job_name: string;
  jobStatusStateName: string;
  creation_time: Date;
  latestJobStatus: { jobState: unknown } | null;
  std_out?: string;
  std_err?: string;
}

interface ExperimentData {
  experiment_id: string;
  experiment_name: string;
  description?: string;
  user_name?: string;
  project_id: string;
  creation_time: Date;
  execution_id?: string;
  isEditable?: boolean;
  isCancelable?: boolean;
  isProgressing?: boolean;
  latestStatus?: { state: unknown };
  experiment_inputs: Array<{
    name: string;
    value: unknown;
    type: { isSimpleValueType: boolean; isFileValueType: boolean };
  }>;
  experiment_outputs: Array<{ name: string; [key: string]: unknown }>;
  errors: Array<{ errorId: string; userFriendlyMessage: string }>;
  user_configuration_data: {
    computational_resource_scheduling: {
      wall_time_limit: number;
      total_cpu_count: number;
      node_count: number;
      total_physical_memory: number;
      queue_name: string;
    };
  };
}

interface LocalFullExperiment {
  experiment: ExperimentData;
  project?: unknown;
  projectName?: string;
  applicationName?: string;
  computeHostName?: string;
  resourceHostId?: string;
  experimentStatusName?: string;
  experimentStatus: { time_of_state_change: Date };
  job_details: JobDetail[];
  input_data_products?: unknown[];
  output_data_products?: unknown[];
}

const experimentStore = useExperimentStore();

const fullExperiment = computed(() => experimentStore.fullExperiment as LocalFullExperiment | null);
const launching = computed(() => experimentStore.launching);
const clonedExperiment = computed(() => experimentStore.clonedExperiment);
const groupResourceProfile = computed(() => experimentStore.groupResourceProfile);
const finishedOrExecuting = computed(() => experimentStore.finishedOrExecuting);
const showQueueSettings = computed(() => experimentStore.showQueueSettings);

const localFullExperiment = computed(() => fullExperiment.value);

const localExperiment = computed(() => localFullExperiment.value!.experiment);

const inputDataProducts = computed<Record<string, unknown[]>>(() => {
  const result: Record<string, unknown[]> = {};
  if (localFullExperiment.value && localFullExperiment.value.input_data_products) {
    localFullExperiment.value.experiment.experiment_inputs.forEach((input) => {
      result[input.name] = getDataProducts(input, localFullExperiment.value!.input_data_products);
    });
  }
  return result;
});

const creationTime = computed(() =>
  relativeTime(localFullExperiment.value!.experiment.creation_time),
);

const lastModifiedTime = computed(() =>
  relativeTime(localFullExperiment.value!.experimentStatus.time_of_state_change),
);

const jobCreationTimes = computed<string[]>(() =>
  localFullExperiment.value!.job_details.map((jobDetail) => relativeTime(jobDetail.creation_time)),
);

const editLink = computed(() =>
  urls.editExperiment(
    localExperiment.value.project_id as string,
    localExperiment.value as unknown as { experiment_id: string },
  ),
);

const isEditable = computed(
  () => localExperiment.value.isEditable && localFullExperiment.value!.applicationName && !launching.value,
);

const isLaunchable = computed(() => isEditable.value);

const isClonable = computed(() => !!localFullExperiment.value!.applicationName);

const isCancelable = computed(() => localExperiment.value.isCancelable);

const failedJobs = computed<JobDetail[]>(() => {
  const fe = fullExperiment.value;
  if (fe && fe.job_details) {
    return fe.job_details.filter(
      (job) =>
        localExperiment.value.latestStatus?.state === models.ExperimentState.FAILED ||
        (job.latestJobStatus?.jobState === models.JobState.FAILED),
    );
  }
  return [];
});

const viewGroupResourceProfileLink = computed(() => {
  const grp = groupResourceProfile.value as Record<string, unknown> | null;
  if (!grp) return null;
  const id = grp.groupResourceProfileId || grp.group_resource_profile_id;
  return id ? `/workspace/group-resource-profiles/${id}/` : null;
});

async function onClone() {
  await experimentStore.clone();
  const exp = clonedExperiment.value as unknown as { project_id: string; experiment_id: string };
  urls.navigateToEditExperiment(exp.project_id, exp);
}

function onLaunch() {
  experimentStore.launch();
}

async function onCancel() {
  await experimentStore.cancel();
  notifications.NotificationList.add(
    new notifications.Notification({
      type: "SUCCESS",
      message: "Cancel-experiment requested",
      duration: 5,
    }),
  );
}

function getDataProducts(
  io: { name: string; value: unknown; type: { isSimpleValueType: boolean; isFileValueType: boolean } },
  collection: unknown[] | undefined,
): unknown[] {
  if (!io.value || !collection) return [];
  let dataProducts: unknown[] | null = null;
  if ((io.type as unknown as Record<string, unknown>).name === "URI_COLLECTION") {
    const dataProductURIs = (io.value as string).split(",");
    dataProducts = dataProductURIs.map((uri) =>
      (collection as Array<Record<string, unknown>>).find((dp) => dp.product_uri === uri),
    ) as unknown[];
  } else {
    const dataProductURI = io.value as string;
    dataProducts = (collection as Array<Record<string, unknown>>).filter(
      (dp) => dp.product_uri === dataProductURI,
    );
  }
  return dataProducts ? dataProducts.filter(Boolean) : [];
}
</script>
