<template>
  <div v-if="localFullExperiment">
    <div class="row">
      <div class="col-auto mr-auto">
        <h1 class="h4 mb-4">
          <slot name="title">Experiment Summary</slot>
        </h1>
      </div>
      <div class="col-auto">
        <share-button :entity-id="experiment.experiment_id" />
        <b-link v-if="isEditable" class="btn btn-primary" :href="editLink">
          Edit
          <i class="fa fa-edit" aria-hidden="true"></i>
        </b-link>
        <b-link v-if="isLaunchable" class="btn btn-primary" @click="onLaunch">
          Launch
          <i class="fa fa-running" aria-hidden="true"></i>
        </b-link>
        <b-btn v-if="isClonable" variant="primary" @click="onClone">
          Clone
          <i class="fa fa-copy" aria-hidden="true"></i>
        </b-btn>
        <b-btn v-if="isCancelable" variant="primary" @click="onCancel">
          Cancel
          <i class="fa fa-window-close" aria-hidden="true"></i>
        </b-btn>
      </div>
    </div>
    <template v-for="output in experiment.experiment_outputs">
      <div class="row" v-if="finishedOrExecuting" :key="output.name">
        <div class="col">
          <output-display-container :experiment-output="output" />
        </div>
      </div>
    </template>
    <div class="row" v-if="finishedOrExecuting">
      <div class="col">
        <experiment-storage-view-container
          :experimentId="experiment.experiment_id"
        />
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
                    <div :title="experiment.experiment_id">
                      {{ experiment.experiment_name }}
                    </div>
                    <small class="text-muted">
                      ID: {{ experiment.experiment_id }} (<clipboard-copy-link
                        :text="experiment.experiment_id"
                        :link-classes="['text-reset']"
                      >
                        copy
                        <span slot="icon"></span>
                        <span slot="tooltip"
                          >Copied ID!</span
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
                  <td v-else class="font-italic text-muted">
                    Unable to load interface
                    {{ localFullExperiment.experiment.executionId }}
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
                    <template
                      v-if="localFullExperiment.experiment.isProgressing"
                    >
                      <i class="fa fa-sync-alt fa-spin"></i>
                      <span class="sr-only">Progressing...</span>
                    </template>
                    {{ localFullExperiment.experimentStatusName }}
                  </td>
                </tr>
                <tr v-if="stages.length > 0">
                  <th scope="row">Tasks</th>
                  <td>
                    <ul class="list-unstyled mb-0">
                      <li
                        v-for="stage in stages"
                        :key="stage.taskId"
                        class="d-flex align-items-start mb-2"
                      >
                        <b-badge
                          :variant="stage.variant"
                          class="mr-2 mt-1 text-uppercase"
                          style="min-width: 6rem"
                          >{{ stage.stateLabel }}</b-badge
                        >
                        <div>
                          <strong>{{ stage.typeLabel }}</strong>
                          <span v-if="stage.reason" class="text-muted">
                            — {{ stage.reason }}</span
                          >
                          <small v-if="stage.time" class="text-muted d-block">{{
                            stage.time
                          }}</small>
                          <div v-if="stage.job" class="mt-1">
                            <b-badge
                              :variant="stage.job.variant"
                              class="mr-2 text-uppercase"
                              style="min-width: 6rem"
                              >{{ stage.job.stateLabel }}</b-badge
                            >
                            <span class="text-muted"
                              >Job {{ stage.job.name }} (ID
                              {{ stage.job.id }})</span
                            >
                            <span v-if="stage.job.reason" class="text-muted">
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
                    <b-link :href="viewGroupResourceProfileLink">
                      {{ groupResourceProfile.group_resource_profile_name }}
                    </b-link>
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
                          <span class="text-break">{{ input.value }}</span>
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
                    <b-card
                      v-for="error in experiment.errors"
                      :key="error.error_id"
                      header="Error"
                    >
                      <p>{{ error.user_friendly_message }}</p>
                    </b-card>
                  </td>
                </tr>
                <template v-if="failedJobs.length > 0">
                  <tr v-for="job in failedJobs" :key="job.job_id">
                    <th scope="row">Job Submission Response</th>
                    <td>
                      <b-card
                        v-if="job.std_out"
                        :header="job.job_name + ' STDOUT'"
                      >
                        <pre class="pre-scrollable">{{ job.std_out }}</pre>
                      </b-card>
                      <b-card
                        v-if="job.std_err"
                        :header="job.job_name + ' STDERR'"
                      >
                        <pre class="pre-scrollable">{{ job.std_err }}</pre>
                      </b-card>
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

<script>
import { models } from "django-airavata-api";
import { components, notifications } from "django-airavata-common-ui";
import OutputDisplayContainer from "./output-displays/OutputDisplayContainer";
import urls from "../../utils/urls";

import moment from "moment";
import ExperimentStorageViewContainer from "../storage/ExperimentStorageViewContainer.vue";
import DataProductViewer from "django-airavata-common-ui/js/components/DataProductViewer.vue";
import { mapActions, mapGetters, mapState } from "vuex";

export default {
  name: "experiment-summary",
  components: {
    "clipboard-copy-link": components.ClipboardCopyLink,
    "share-button": components.ShareButton,
    OutputDisplayContainer,
    ExperimentStorageViewContainer,
    DataProductViewer,
  },
  computed: {
    ...mapState("viewExperiment", [
      "fullExperiment",
      "launching",
      "clonedExperiment",
      "groupResourceProfile",
    ]),
    ...mapGetters("viewExperiment", [
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
              this.localFullExperiment.input_data_products
            );
          }
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
              this.localFullExperiment.output_data_products
            );
          }
        );
      }
      return result;
    },
    creationTime: function () {
      return moment(this.localFullExperiment.experiment.creation_time).fromNow();
    },
    lastModifiedTime: function () {
      return moment(
        this.localFullExperiment.experimentStatus.time_of_state_change
      ).fromNow();
    },
    experiment: function () {
      return this.localFullExperiment.experiment;
    },
    jobCreationTimes: function () {
      return this.localFullExperiment.job_details.map((jobDetail) =>
        moment(jobDetail.creation_time).fromNow()
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
            variant: this.taskStateVariant(stateName),
            reason: latest ? latest.reason : "",
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
              variant: this.jobStateVariant(jobStateName),
              reason: js ? js.reason : "",
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
              job.latestJobStatus.job_state === models.JobState.FAILED)
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
    ...mapActions("viewExperiment", ["clone", "launch", "cancel"]),
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
        })
      );
    },
    getDataProducts(io, collection) {
      if (!io.value || !collection) {
        return [];
      }
      let dataProducts = null;
      if (io.type === models.DataType.URI_COLLECTION) {
        const dataProductURIs = io.value.split(",");
        dataProducts = dataProductURIs.map((uri) =>
          collection.find((dp) => dp.product_uri === uri)
        );
      } else {
        const dataProductURI = io.value;
        dataProducts = collection.filter(
          (dp) => dp.product_uri === dataProductURI
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
    taskStateVariant(stateName) {
      switch (stateName) {
        case "TASK_STATE_COMPLETED":
          return "success";
        case "TASK_STATE_EXECUTING":
          return "info";
        case "TASK_STATE_FAILED":
          return "danger";
        case "TASK_STATE_CANCELED":
          return "warning";
        case "TASK_STATE_CREATED":
          return "secondary";
        default:
          return "light";
      }
    },
    jobStateVariant(jobStateName) {
      switch (jobStateName) {
        case "COMPLETE":
          return "success";
        case "ACTIVE":
          return "info";
        case "SUBMITTED":
        case "QUEUED":
          return "secondary";
        case "FAILED":
        case "NON_CRITICAL_FAIL":
          return "danger";
        case "CANCELED":
        case "SUSPENDED":
          return "warning";
        default:
          return "light";
      }
    },
  },
};
</script>
