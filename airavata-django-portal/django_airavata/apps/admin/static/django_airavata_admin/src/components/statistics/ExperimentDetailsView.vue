<template>
  <div>
    <table class="details-table" v-if="fullExperiment">
      <tbody>
        <tr>
          <th scope="row">Name</th>
          <td>
            <div :title="experiment.experiment_id">
              {{ experiment.experiment_name }}
            </div>
            <small class="text-sm text-muted-foreground">
              ID: {{ experiment.experiment_id }} (<clipboard-copy-link
                :text="experiment.experiment_id"
                :link-classes="['text-muted-foreground']"
              >
                copy
                <template v-slot:icon>
                  <span></span>
                </template>
                <template v-slot:tooltip>
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
          <td v-if="fullExperiment.applicationName">
            {{ fullExperiment.applicationName }}
          </td>
          <td v-else class="text-muted-foreground italic">
            Unable to load interface
            {{ fullExperiment.experiment.execution_id }}
          </td>
        </tr>
        <tr>
          <th scope="row">Compute Resource</th>
          <td v-if="fullExperiment.computeHostName">
            {{ fullExperiment.computeHostName }}
          </td>
          <td v-else class="text-muted-foreground italic">
            Unable to load compute resource {{ fullExperiment.resourceHostId }}
          </td>
        </tr>
        <tr>
          <th scope="row">Experiment Status</th>
          <td>
            <template v-if="fullExperiment.experiment.isProgressing">
              <RefreshCw class="inline size-4 animate-spin" />
              <span class="sr-only">Progressing...</span>
            </template>
            {{ fullExperiment.experimentStatusName }}
          </td>
        </tr>
        <tr
          v-if="
            fullExperiment.job_details && fullExperiment.job_details.length > 0
          "
        >
          <th scope="row">Job</th>
          <td>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>ID</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Creation Time</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                <TableRow
                  v-for="(jobDetail, index) in fullExperiment.job_details"
                  :key="jobDetail.job_id"
                >
                  <TableCell>{{ jobDetail.job_name }}</TableCell>
                  <TableCell>{{ jobDetail.job_id }}</TableCell>
                  <TableCell>{{ jobDetail.jobStatusStateName }}</TableCell>
                  <TableCell>
                    <span :title="jobDetail.creation_time.toString()">{{
                      jobCreationTimes[index]
                    }}</span>
                  </TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </td>
        </tr>
        <tr>
          <th scope="row">Notification List</th>
          <td>
            {{
              experiment.email_addresses
                ? experiment.email_addresses.join(", ")
                : ""
            }}
          </td>
        </tr>
        <tr
          v-if="
            fullExperiment.job_details && fullExperiment.job_details.length > 0
          "
        >
          <th scope="row">Working Dir</th>
          <td>
            <div
              v-for="jobDetail in fullExperiment.job_details"
              :key="jobDetail.job_id"
            >
              {{ jobDetail.job_name }}: {{ jobDetail.working_dir }}
            </div>
          </td>
        </tr>
        <tr
          v-if="
            fullExperiment.job_details && fullExperiment.job_details.length > 0
          "
        >
          <th scope="row">Job Description</th>
          <td>
            <Card
              v-for="jobDetail in fullExperiment.job_details"
              :key="jobDetail.job_id"
            >
              <CardHeader>
                <CardTitle>{{ jobDetail.job_name }}</CardTitle>
              </CardHeader>
              <CardContent>
                <pre>{{ jobDetail.job_description }}</pre>
              </CardContent>
            </Card>
          </td>
        </tr>
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
                fullExperiment.experimentStatus.time_of_state_change.toString()
              "
              >{{ lastModifiedTime }}</span
            >
          </td>
        </tr>
        <tr>
          <th scope="row">Wall Time Limit</th>
          <td>
            {{
              experiment.user_configuration_data
                .computational_resource_scheduling.wall_time_limit
            }}
            minutes
          </td>
        </tr>
        <tr>
          <th scope="row">CPU Count</th>
          <td>
            {{
              experiment.user_configuration_data
                .computational_resource_scheduling.total_cpu_count
            }}
          </td>
        </tr>
        <tr>
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
            experiment.user_configuration_data.computational_resource_scheduling
              .total_physical_memory
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
        <tr>
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
          <th scope="row">Outputs</th>
          <td>
            <ul>
              <li
                v-for="output in experiment.experiment_outputs"
                :key="output.name"
              >
                {{ output.name }}:
                <template v-if="output.type.isSimpleValueType">
                  <span class="text-break">{{ output.value }}</span>
                </template>
                <data-product-viewer
                  v-for="dp in outputDataProducts[output.name]"
                  v-else-if="output.type.isFileValueType"
                  :data-product="dp"
                  :key="dp.product_uri"
                />
              </li>
            </ul>
          </td>
        </tr>
        <tr>
          <th scope="row">Experiment Data Dir</th>
          <td>
            <div>{{ experimentDataDir }}</div>
            <Alert
              v-if="archived"
              class="mt-2 border-transparent bg-warning text-warning-foreground"
            >
              <AlertDescription class="text-warning-foreground">
                This directory was archived in
                <b>{{ experimentArchive.archive_name }}</b> on
                {{ experimentArchive.created_date }}.
              </AlertDescription>
            </Alert>
          </td>
        </tr>
        <tr>
          <th scope="row">Errors</th>
          <td>
            <Card v-for="error in experiment.errors" :key="error.error_id">
              <CardHeader>
                <CardTitle>Error</CardTitle>
              </CardHeader>
              <CardContent>
                <p>{{ error.user_friendly_message }}</p>
                <pre class="max-h-80 overflow-auto">{{
                  error.actual_error_message
                }}</pre>
              </CardContent>
            </Card>
          </td>
        </tr>
        <template v-if="failedJobs.length > 0">
          <tr v-for="job in failedJobs" :key="job.job_id">
            <th scope="row">Job Submission Response</th>
            <td>
              <Card v-if="job.std_out">
                <CardHeader>
                  <CardTitle>{{ job.job_name + " STDOUT" }}</CardTitle>
                </CardHeader>
                <CardContent>
                  <pre class="max-h-80 overflow-auto">{{ job.std_out }}</pre>
                </CardContent>
              </Card>
              <Card v-if="job.std_err">
                <CardHeader>
                  <CardTitle>{{ job.job_name + " STDERR" }}</CardTitle>
                </CardHeader>
                <CardContent>
                  <pre class="max-h-80 overflow-auto">{{ job.std_err }}</pre>
                </CardContent>
              </Card>
            </td>
          </tr>
        </template>
      </tbody>
    </table>
    <h2 class="mb-3 text-lg font-semibold">Process Details</h2>
    <Card
      v-for="process in experiment.processes"
      :key="process.process_id"
      class="mb-3"
    >
      <CardHeader>
        <CardTitle>{{ process.process_id }}</CardTitle>
      </CardHeader>
      <CardContent class="space-y-3">
        <Card v-for="task in process.sortedTasks" :key="task.task_id">
          <CardHeader>
            <CardTitle>{{ task.task_id }}</CardTitle>
          </CardHeader>
          <CardContent>
            <table class="details-table">
              <tbody>
                <tr>
                  <th scope="row">Task Id</th>
                  <td>{{ task.task_id }}</td>
                </tr>
                <tr>
                  <th scope="row">Task Type</th>
                  <td>{{ task.task_type.name }}</td>
                </tr>
                <tr>
                  <th scope="row">Task Status</th>
                  <td>{{ task.latestStatus.state.name }}</td>
                </tr>
                <tr>
                  <th scope="row">Task Status Time</th>
                  <td>
                    <human-date
                      :date="task.latestStatus.time_of_state_change"
                    />
                  </td>
                </tr>
                <tr>
                  <th scope="row">Task Status Reason</th>
                  <td>{{ task.latestStatus.reason }}</td>
                </tr>
                <template
                  v-if="task.task_errors && task.task_errors.length > 0"
                >
                  <tr>
                    <th scope="row">Task Errors</th>
                    <td>
                      <Card
                        v-for="error in task.task_errors"
                        :key="error.error_id"
                      >
                        <CardHeader>
                          <CardTitle>{{ error.error_id }}</CardTitle>
                        </CardHeader>
                        <CardContent>
                          <p>{{ error.user_friendly_message }}</p>
                          <pre class="max-h-80 overflow-auto">{{
                            error.actual_error_message
                          }}</pre>
                        </CardContent>
                      </Card>
                    </td>
                  </tr>
                </template>
                <template v-if="task.jobs && task.jobs.length > 0">
                  <tr>
                    <th scope="row">Jobs</th>
                    <td>
                      <Card v-for="job in task.jobs" :key="job.job_id">
                        <CardHeader>
                          <CardTitle>{{ job.job_name }}</CardTitle>
                        </CardHeader>
                        <CardContent>
                          <pre>{{ job.job_description }}</pre>
                        </CardContent>
                      </Card>
                    </td>
                  </tr>
                </template>
              </tbody>
            </table>
          </CardContent>
        </Card>

        <Card v-for="error in process.process_errors" :key="error.error_id">
          <CardHeader>
            <CardTitle>{{ "Process Error " + error.error_id }}</CardTitle>
          </CardHeader>
          <CardContent>
            <p>{{ error.user_friendly_message }}</p>
            <pre class="max-h-80 overflow-auto">{{
              error.actual_error_message
            }}</pre>
          </CardContent>
        </Card>
      </CardContent>
    </Card>
  </div>
</template>

<script>
import { RefreshCw } from "@lucide/vue";
import { models, services } from "django-airavata-api";
import { components } from "django-airavata-common-ui";

import moment from "moment";

export default {
  name: "experiment-details-view",
  props: {
    experiment: {
      type: models.Experiment,
      required: true,
    },
  },
  components: {
    RefreshCw,
    "clipboard-copy-link": components.ClipboardCopyLink,
    "data-product-viewer": components.DataProductViewer,
    "human-date": components.HumanDate,
  },
  data() {
    return {
      fullExperiment: null,
      experimentArchive: null,
    };
  },
  computed: {
    inputDataProducts() {
      const result = {};
      if (this.fullExperiment && this.fullExperiment.input_data_products) {
        this.fullExperiment.experiment.experiment_inputs.forEach((input) => {
          result[input.name] = this.getDataProducts(
            input,
            this.fullExperiment.input_data_products,
          );
        });
      }
      return result;
    },
    outputDataProducts() {
      const result = {};
      if (this.fullExperiment && this.fullExperiment.output_data_products) {
        this.fullExperiment.experiment.experiment_outputs.forEach((output) => {
          result[output.name] = this.getDataProducts(
            output,
            this.fullExperiment.output_data_products,
          );
        });
      }
      return result;
    },
    creationTime: function () {
      return moment(this.fullExperiment.experiment.creation_time).fromNow();
    },
    lastModifiedTime: function () {
      return moment(
        this.fullExperiment.experimentStatus.time_of_state_change,
      ).fromNow();
    },
    jobCreationTimes: function () {
      return this.fullExperiment.job_details.map((jobDetail) =>
        moment(jobDetail.creation_time).fromNow(),
      );
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
    experimentDataDir() {
      if (this.experiment && this.experiment.user_configuration_data) {
        return this.experiment.user_configuration_data.experiment_data_dir;
      } else {
        return null;
      }
    },
    archived() {
      return this.experimentArchive?.archived;
    },
  },
  created() {
    services.FullExperimentService.retrieve({
      lookup: this.experiment.experiment_id,
    }).then((fullExperiment) => (this.fullExperiment = fullExperiment));
    services.ExperimentArchiveService.get({
      experimentId: this.experiment.experiment_id,
    }).then((result) => {
      this.experimentArchive = result;
    });
  },
  methods: {
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
  },
};
</script>

<style scoped>
/* Key/value details layout: a fixed-width row label and a value column. Styled
   locally (not via Bootstrap) so it matches the design system's muted labels. */
.details-table {
  width: 100%;
  table-layout: fixed;
}
.details-table th[scope="row"] {
  width: 20%;
  padding: 0.5rem 0.75rem 0.5rem 0;
  text-align: left;
  font-weight: 600;
  vertical-align: top;
}
.details-table td {
  padding: 0.5rem 0;
  vertical-align: top;
}
</style>
