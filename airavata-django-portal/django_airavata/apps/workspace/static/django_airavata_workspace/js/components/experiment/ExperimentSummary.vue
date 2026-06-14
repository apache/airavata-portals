<template>
  <main-layout
    v-if="localFullExperiment"
    subtitle="Review experiment details, status, and outputs."
  >
    <template #title>
      <h1 class="text-2xl font-semibold tracking-tight text-foreground">
        <slot name="title">Experiment Summary</slot>
      </h1>
    </template>
    <template #actions>
      <share-button :entity-id="experiment.experiment_id" />
      <Button v-if="isEditable" as="a" variant="outline" :href="editLink">
        Edit
        <Pencil class="size-4" aria-hidden="true" />
      </Button>
      <Button v-if="isLaunchable" variant="default" @click="onLaunch">
        Launch
        <Play class="size-4" aria-hidden="true" />
      </Button>
      <Button v-if="isClonable" variant="outline" @click="onClone">
        Clone
        <Copy class="size-4" aria-hidden="true" />
      </Button>
      <Button v-if="isCancelable" variant="destructive" @click="onCancel">
        Cancel
        <XSquare class="size-4" aria-hidden="true" />
      </Button>
    </template>
    <template v-for="output in experiment.experiment_outputs">
      <div class="mt-4" v-if="finishedOrExecuting" :key="output.name">
        <output-display-container :experiment-output="output" />
      </div>
    </template>
    <div class="mt-4" v-if="finishedOrExecuting">
      <experiment-storage-view-container
        :experimentId="experiment.experiment_id"
      />
    </div>
    <div class="mt-4">
      <Card>
        <CardContent>
          <table class="w-full text-sm">
            <tbody>
              <tr>
                <th scope="row">Name</th>
                <td>
                  <div :title="experiment.experiment_id">
                    {{ experiment.experiment_name }}
                  </div>
                  <small class="text-muted-foreground">
                    ID: {{ experiment.experiment_id }} (<clipboard-copy-link
                      :text="experiment.experiment_id"
                      :link-classes="['text-inherit']"
                    >
                      copy
                      <template #icon><span></span></template>
                      <template #tooltip
                        ><span>Copied ID!</span></template
                      > </clipboard-copy-link
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
                <td v-if="localFullExperiment.project">
                  {{ localFullExperiment.projectName }}
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
                <td v-if="localFullExperiment.applicationName">
                  {{ localFullExperiment.applicationName }}
                </td>
                <td v-else class="text-muted-foreground italic">
                  Unable to load interface
                  {{ localFullExperiment.experiment.executionId }}
                </td>
              </tr>
              <tr>
                <th scope="row">Compute Resource</th>
                <td v-if="localFullExperiment.computeHostName">
                  {{ localFullExperiment.computeHostName }}
                </td>
                <td v-else class="text-muted-foreground italic">
                  Unable to load compute resource
                  {{ localFullExperiment.resourceHostId }}
                </td>
              </tr>
              <tr>
                <th scope="row">Experiment Status</th>
                <td>
                  <template v-if="localFullExperiment.experiment.isProgressing">
                    <RefreshCw class="inline size-4 animate-spin" />
                    <span class="sr-only">Progressing...</span>
                  </template>
                  {{ localFullExperiment.experimentStatusName }}
                </td>
              </tr>
              <tr v-if="stages.length > 0">
                <th scope="row">Progress</th>
                <td>
                  <ul class="timeline list-unstyled mb-0">
                    <li
                      v-for="stage in stages"
                      :key="stage.taskId"
                      class="timeline-item"
                    >
                      <div class="timeline-marker">
                        <span
                          v-if="stage.kind === 'running'"
                          class="timeline-node timeline-node--running"
                          :title="stage.taskId"
                        >
                          <LoaderCircle class="size-4 animate-spin" />
                        </span>
                        <span
                          v-else
                          class="timeline-node timeline-dot"
                          :class="'timeline-dot--' + stage.kind"
                          :title="stage.taskId"
                        ></span>
                        <span class="sr-only">{{ stage.stateLabel }}</span>
                      </div>
                      <div class="timeline-content">
                        <strong>{{ stage.typeLabel }}</strong>
                        <span v-if="stage.reason" class="text-muted-foreground">
                          — {{ stage.reason }}</span
                        >
                        <small
                          v-if="stage.time"
                          class="block text-muted-foreground"
                          >{{ stage.time }}</small
                        >
                        <div v-if="stage.job" class="mt-1 text-sm">
                          <span
                            class="timeline-dot timeline-dot--inline"
                            :class="'timeline-dot--' + stage.job.kind"
                          ></span>
                          <span class="text-muted-foreground"
                            >Job {{ stage.job.name }} (ID
                            {{ stage.job.id }})</span
                          >
                          <span
                            v-if="stage.job.reason"
                            class="text-muted-foreground"
                          >
                            — {{ stage.job.reason }}</span
                          >
                        </div>
                      </div>
                    </li>
                  </ul>
                </td>
              </tr>
              <!--  TODO: leave this out for now -->
              <!-- <tr>
                                    <th scope="row">Notification List</th>
                                    <td>{{ experiment.emailAddresses
                                            ? experiment.emailAddresses.join(", ")
                                            : '' }}</td>
                                </tr> -->
              <tr>
                <th scope="row">Creation Time</th>
                <td>
                  <span :title="experiment.creation_time.toString()">{{
                    creationTime
                  }}</span>
                </td>
              </tr>
              <tr>
                <th scope="row">Last Modified Time</th>
                <td>
                  <span
                    :title="
                      localFullExperiment.experimentStatus.time_of_state_change.toString()
                    "
                    >{{ lastModifiedTime }}</span
                  >
                </td>
              </tr>
              <tr v-if="groupResourceProfile">
                <th scope="row">Allocation</th>
                <td>
                  <a class="text-primary" :href="viewGroupResourceProfileLink">
                    {{ groupResourceProfile.group_resource_profile_name }}
                  </a>
                </td>
              </tr>
              <tr v-if="showQueueSettings">
                <th scope="row">Wall Time Limit</th>
                <td>
                  {{
                    experiment.user_configuration_data
                      .computational_resource_scheduling.wall_time_limit
                  }}
                  minutes
                </td>
              </tr>
              <tr v-if="showQueueSettings">
                <th scope="row">CPU Count</th>
                <td>
                  {{
                    experiment.user_configuration_data
                      .computational_resource_scheduling.total_cpu_count
                  }}
                </td>
              </tr>
              <tr v-if="showQueueSettings">
                <th scope="row">Node Count</th>
                <td>
                  {{
                    experiment.user_configuration_data
                      .computational_resource_scheduling.node_count
                  }}
                </td>
              </tr>
              <tr
                v-if="
                  showQueueSettings &&
                  experiment.user_configuration_data
                    .computational_resource_scheduling.total_physical_memory
                "
              >
                <th scope="row">Total Physical Memory</th>
                <td>
                  {{
                    experiment.user_configuration_data.computational_resource_scheduling.total_physical_memory.toLocaleString()
                  }}
                  MB
                </td>
              </tr>
              <tr v-if="showQueueSettings">
                <th scope="row">Queue</th>
                <td>
                  {{
                    experiment.user_configuration_data
                      .computational_resource_scheduling.queue_name
                  }}
                </td>
              </tr>
              <tr>
                <th scope="row">Inputs</th>
                <td>
                  <ul>
                    <li
                      v-for="input in experiment.experiment_inputs"
                      :key="input.name"
                    >
                      {{ input.name }}:
                      <template v-if="input.type.isSimpleValueType">
                        <span class="break-words">{{ input.value }}</span>
                      </template>
                      <data-product-viewer
                        v-for="dp in inputDataProducts[input.name]"
                        v-else-if="input.type.isFileValueType"
                        :data-product="dp"
                        :input-file="true"
                        :key="dp.product_uri"
                      />
                    </li>
                  </ul>
                </td>
              </tr>
              <tr>
                <th scope="row">Errors</th>
                <td>
                  <Card
                    v-for="error in experiment.errors"
                    :key="error.error_id"
                    class="mb-2"
                  >
                    <CardHeader class="border-b">
                      <CardTitle class="text-base">Error</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <p>{{ error.user_friendly_message }}</p>
                    </CardContent>
                  </Card>
                </td>
              </tr>
              <template v-if="failedJobs.length > 0">
                <tr v-for="job in failedJobs" :key="job.job_id">
                  <th scope="row">Job Submission Response</th>
                  <td>
                    <Card v-if="job.std_out" class="mb-2">
                      <CardHeader class="border-b">
                        <CardTitle class="text-base"
                          >{{ job.job_name }} STDOUT</CardTitle
                        >
                      </CardHeader>
                      <CardContent>
                        <pre class="max-h-[340px] overflow-auto">{{
                          job.std_out
                        }}</pre>
                      </CardContent>
                    </Card>
                    <Card v-if="job.std_err" class="mb-2">
                      <CardHeader class="border-b">
                        <CardTitle class="text-base"
                          >{{ job.job_name }} STDERR</CardTitle
                        >
                      </CardHeader>
                      <CardContent>
                        <pre class="max-h-[340px] overflow-auto">{{
                          job.std_err
                        }}</pre>
                      </CardContent>
                    </Card>
                  </td>
                </tr>
              </template>
            </tbody>
          </table>
        </CardContent>
      </Card>
    </div>
  </main-layout>
</template>

<script>
import {
  Copy,
  LoaderCircle,
  Pencil,
  Play,
  RefreshCw,
  XSquare,
} from "@lucide/vue";
import { models } from "django-airavata-api";
import { components, notifications } from "django-airavata-common-ui";
import OutputDisplayContainer from "./output-displays/OutputDisplayContainer";
import urls from "../../utils/urls";

import moment from "moment";
import ExperimentStorageViewContainer from "../storage/ExperimentStorageViewContainer.vue";
import DataProductViewer from "django-airavata-common-ui/js/components/DataProductViewer.vue";
import { mapActions, mapState } from "pinia";
import { useViewExperimentStore } from "../../store";

export default {
  name: "experiment-summary",
  components: {
    Copy,
    LoaderCircle,
    Pencil,
    Play,
    RefreshCw,
    XSquare,
    "clipboard-copy-link": components.ClipboardCopyLink,
    "main-layout": components.MainLayout,
    "share-button": components.ShareButton,
    OutputDisplayContainer,
    ExperimentStorageViewContainer,
    DataProductViewer,
  },
  computed: {
    ...mapState(useViewExperimentStore, [
      "fullExperiment",
      "launching",
      "clonedExperiment",
      "groupResourceProfile",
      "finishedOrExecuting",
      "showQueueSettings",
    ]),
    localFullExperiment() {
      return this.fullExperiment;
    },
    inputDataProducts() {
      const result = {};
      if (
        this.localFullExperiment &&
        this.localFullExperiment.input_data_products
      ) {
        this.localFullExperiment.experiment.experiment_inputs.forEach(
          (input) => {
            result[input.name] = this.getDataProducts(
              input,
              this.localFullExperiment.input_data_products,
            );
          },
        );
      }
      return result;
    },
    outputDataProducts() {
      const result = {};
      if (
        this.localFullExperiment &&
        this.localFullExperiment.output_data_products
      ) {
        this.localFullExperiment.experiment.experiment_outputs.forEach(
          (output) => {
            result[output.name] = this.getDataProducts(
              output,
              this.localFullExperiment.output_data_products,
            );
          },
        );
      }
      return result;
    },
    creationTime: function () {
      return moment(
        this.localFullExperiment.experiment.creation_time,
      ).fromNow();
    },
    lastModifiedTime: function () {
      return moment(
        this.localFullExperiment.experimentStatus.time_of_state_change,
      ).fromNow();
    },
    experiment: function () {
      return this.localFullExperiment.experiment;
    },
    jobCreationTimes: function () {
      return this.localFullExperiment.job_details.map((jobDetail) =>
        moment(jobDetail.creation_time).fromNow(),
      );
    },
    // The experiment's PROCESS -> TASK pipeline as an ordered stage list (env setup, data
    // staging, job submission, monitoring), each with its current state, the latest reason, and
    // timing. The job (with its own live status) is nested under the Job Submission stage. Surfaces
    // exactly which stage the experiment is in instead of a single job row frozen at QUEUED.
    stages() {
      const exp =
        this.localFullExperiment && this.localFullExperiment.experiment;
      if (!exp || !exp.processes || exp.processes.length === 0) {
        return [];
      }
      const result = [];
      exp.processes.forEach((process) => {
        process.sortedTasks.forEach((task) => {
          const latest = task.latestStatus;
          const stateName = latest && latest.state ? latest.state.name : null;
          const stage = {
            taskId: task.task_id,
            typeLabel: this.taskTypeLabel(task.task_type),
            stateLabel: this.taskStateLabel(stateName),
            kind: this.taskStateKind(stateName),
            reason: this.cleanReason(latest ? latest.reason : ""),
            time:
              latest && latest.time_of_state_change
                ? moment(latest.time_of_state_change).fromNow()
                : "",
            job: null,
          };
          if (task.jobs && task.jobs.length > 0) {
            const job = task.jobs[0];
            const js = job.latestJobStatus;
            const jobStateName = js && js.job_state ? js.job_state.name : null;
            stage.job = {
              id: job.job_id,
              name: job.job_name,
              stateLabel: this.titleCase(jobStateName) || "Pending",
              kind: this.jobStateKind(jobStateName),
              reason: this.cleanReason(js ? js.reason : ""),
            };
          }
          result.push(stage);
        });
      });
      return result;
    },
    editLink() {
      return urls.editExperiment(this.experiment);
    },
    isEditable() {
      return (
        this.experiment.isEditable &&
        this.localFullExperiment.applicationName &&
        !this.launching
      );
    },
    isLaunchable() {
      return this.isEditable;
    },
    isClonable() {
      return this.localFullExperiment.applicationName;
    },
    isCancelable() {
      return this.localFullExperiment.experiment.isCancelable;
    },
    failedJobs() {
      if (this.fullExperiment && this.fullExperiment.job_details) {
        return this.fullExperiment.job_details.filter(
          (job) =>
            this.experiment.latestStatus.state ===
              models.ExperimentState.FAILED ||
            (job.latestJobStatus &&
              job.latestJobStatus.job_state === models.JobState.FAILED),
        );
      } else {
        return [];
      }
    },
    viewGroupResourceProfileLink() {
      return this.groupResourceProfile
        ? urls.viewGroupResourceProfile(this.groupResourceProfile)
        : null;
    },
  },
  methods: {
    ...mapActions(useViewExperimentStore, ["clone", "launch", "cancel"]),
    async onClone() {
      await this.clone();
      urls.navigateToEditExperiment(this.clonedExperiment);
    },
    onLaunch() {
      this.launch();
    },
    async onCancel() {
      await this.cancel();
      notifications.NotificationList.add(
        new notifications.Notification({
          type: "SUCCESS",
          message: "Cancel-experiment requested",
          duration: 5,
        }),
      );
    },
    getDataProducts(io, collection) {
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
        dataProducts = collection.filter(
          (dp) => dp.product_uri === dataProductURI,
        );
      }
      return dataProducts
        ? dataProducts.filter((dp) => (dp ? true : false))
        : [];
    },
    titleCase(s) {
      if (!s) return "";
      return s
        .toLowerCase()
        .split("_")
        .map((w) => (w ? w.charAt(0).toUpperCase() + w.slice(1) : ""))
        .join(" ");
    },
    taskTypeLabel(taskType) {
      const name = taskType && taskType.name ? taskType.name : "";
      const labels = {
        ENV_SETUP: "Environment Setup",
        DATA_STAGING: "Data Staging",
        JOB_SUBMISSION: "Job Submission",
        ENV_CLEANUP: "Environment Cleanup",
        MONITORING: "Job Monitoring",
        OUTPUT_FETCHING: "Output Fetching",
      };
      return labels[name] || this.titleCase(name) || "Task";
    },
    taskStateLabel(stateName) {
      if (!stateName) return "Pending";
      return this.titleCase(stateName.replace(/^TASK_STATE_/, ""));
    },
    // Normalize task/job states to a small set of timeline "kinds" that map to a dot
    // color (completed=green, failed=red, canceled=yellow, pending=gray) or a spinner
    // (running) in the Progress timeline.
    taskStateKind(stateName) {
      switch (stateName) {
        case "TASK_STATE_COMPLETED":
          return "completed";
        case "TASK_STATE_EXECUTING":
          return "running";
        case "TASK_STATE_FAILED":
          return "failed";
        case "TASK_STATE_CANCELED":
          return "canceled";
        default:
          // TASK_STATE_CREATED, null, or anything not yet started.
          return "pending";
      }
    },
    jobStateKind(jobStateName) {
      switch (jobStateName) {
        case "COMPLETE":
          return "completed";
        case "ACTIVE":
          return "running";
        case "FAILED":
        case "NON_CRITICAL_FAIL":
          return "failed";
        case "CANCELED":
        case "SUSPENDED":
          return "canceled";
        default:
          // SUBMITTED, QUEUED, null — waiting to start.
          return "pending";
      }
    },
    cleanReason(reason) {
      if (!reason) return "";
      // The server embeds the raw task id in some status reasons; the id is surfaced via
      // the timeline node tooltip instead, so strip it from the human-readable text.
      return reason
        .replace(/\bTASK_[0-9A-Za-z-]+/g, "")
        .replace(/\s{2,}/g, " ")
        .trim();
    },
  },
};
</script>

<style scoped>
/* Replaces Bootstrap's `.table` styling for the summary key/value table after the
   Tailwind migration: bordered rows with a bold, top-aligned header column. */
table tbody tr {
  border-bottom: 1px solid var(--border);
}
table tbody tr:last-child {
  border-bottom: 0;
}
table th[scope="row"] {
  text-align: left;
  font-weight: 600;
  vertical-align: top;
  padding: 0.5rem 0.75rem 0.5rem 0;
  white-space: nowrap;
}
table td {
  vertical-align: top;
  padding: 0.5rem 0;
}

/* Vertical timeline for the experiment Progress (PROCESS -> TASK pipeline). Each task is a
   node (colored dot, or a spinner while running) connected by a vertical line. */
.timeline {
  position: relative;
}
.timeline-item {
  display: flex;
  align-items: stretch;
}
.timeline-item:not(:last-child) {
  padding-bottom: 0.75rem;
}
.timeline-marker {
  position: relative;
  flex: 0 0 1.25rem;
  display: flex;
  justify-content: center;
}
/* the connector line running vertically through the nodes */
.timeline-marker::before {
  content: "";
  position: absolute;
  top: 0;
  bottom: 0;
  left: 50%;
  width: 2px;
  margin-left: -1px;
  background-color: #dee2e6;
}
/* trim the line so it starts/ends at the first/last node instead of overshooting */
.timeline-item:first-child .timeline-marker::before {
  top: 0.7rem;
}
.timeline-item:last-child .timeline-marker::before {
  bottom: auto;
  height: 0.7rem;
}
.timeline-node {
  position: relative;
  z-index: 1;
  margin-top: 0.2rem;
  box-shadow: 0 0 0 2px #fff;
}
.timeline-dot {
  width: 0.85rem;
  height: 0.85rem;
  border-radius: 50%;
  background-color: #adb5bd;
}
.timeline-dot--completed {
  background-color: #28a745;
}
.timeline-dot--failed {
  background-color: #dc3545;
}
.timeline-dot--canceled {
  background-color: #ffc107;
}
.timeline-dot--running {
  background-color: #007bff;
}
.timeline-dot--pending {
  background-color: #adb5bd;
}
.timeline-node--running {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 1rem;
  height: 1rem;
  border-radius: 50%;
  background-color: #fff;
  color: #007bff;
  font-size: 0.95rem;
}
.timeline-content {
  padding-left: 0.5rem;
}
/* small inline dot used for the nested SLURM job state */
.timeline-dot--inline {
  display: inline-block;
  width: 0.6rem;
  height: 0.6rem;
  margin-top: 0;
  margin-right: 0.25rem;
  box-shadow: none;
  vertical-align: middle;
}
</style>
