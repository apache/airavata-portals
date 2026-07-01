<template>
  <main-layout
    title="Experiments"
    subtitle="Browse and manage your experiments."
  >
    <div class="space-y-6">
      <Card>
        <CardContent>
          <div class="mb-2 flex w-full flex-wrap items-center gap-2">
            <Input
              v-if="defaultOptionSelected"
              class="w-auto flex-1"
              v-model="search"
              placeholder="Search Experiments"
              @keydown.enter="searchExperiments"
            />
            <select
              v-if="applicationSelected"
              v-model="applicationSelect"
              :class="selectClass"
            >
              <option :value="null" disabled>
                Select an application to search by
              </option>
              <option
                v-for="option in applicationNameOptions"
                :key="option.value"
                :value="option.value"
              >
                {{ option.text }}
              </option>
            </select>
            <select
              v-if="projectSelected"
              v-model="projectSelect"
              :class="selectClass"
            >
              <option :value="null" disabled>
                Select a project to search by
              </option>
              <option
                v-for="option in projectNameOptions"
                :key="option.value"
                :value="option.value"
              >
                {{ option.text }}
              </option>
            </select>
            <select
              v-model="experimentAttributeSelect"
              :class="selectClass"
              @change="checkSearchOptions"
            >
              <option :value="null" disabled>
                Select an attribute to search by
              </option>
              <option value="USER_NAME">User Name</option>
              <option value="EXPERIMENT_NAME">Experiment Name</option>
              <option value="EXPERIMENT_DESC">Experiment Description</option>
              <option value="APPLICATION_ID">Application</option>
              <option value="PROJECT_ID">Project</option>
              <option value="JOB_ID">Job Id</option>
            </select>
            <select v-model="experimentStatusSelect" :class="selectClass">
              <option :value="null" disabled>
                Select an experiment status to filter by
              </option>
              <option value="ALL">ALL</option>
              <option value="EXPERIMENT_STATE_CREATED">Created</option>
              <option value="EXPERIMENT_STATE_VALIDATED">Validated</option>
              <option value="EXPERIMENT_STATE_SCHEDULED">Scheduled</option>
              <option value="EXPERIMENT_STATE_LAUNCHED">Launched</option>
              <option value="EXPERIMENT_STATE_EXECUTING">Executing</option>
              <option value="EXPERIMENT_STATE_CANCELED">Canceled</option>
              <option value="EXPERIMENT_STATE_COMPLETED">Completed</option>
              <option value="EXPERIMENT_STATE_FAILED">Failed</option>
            </select>
            <Button variant="outline" @click="resetSearch">Reset</Button>
            <Button variant="default" @click="searchExperiments">Search</Button>
          </div>
          <div class="mb-2 flex w-full items-stretch">
            <span
              class="flex items-center rounded-l-md border border-r-0 border-input px-3 text-muted-foreground"
            >
              <CalendarDays class="size-4" aria-hidden="true" />
            </span>
            <flat-pickr
              v-model="dateSelect"
              :config="dateConfig"
              placeholder="Select a date range to filter by"
              @on-change="dateRangeChanged"
              class="h-9 w-full min-w-0 rounded-r-md border border-input bg-transparent px-3 py-1 text-sm shadow-xs outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50"
            />
          </div>
        </CardContent>
      </Card>
      <Card>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Application</TableHead>
                <TableHead>User</TableHead>
                <TableHead>Creation Time</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              <TableRow
                v-for="experiment in experiments"
                :key="experiment.experiment_id"
              >
                <TableCell>
                  <a class="text-primary" :href="viewLink(experiment)">{{
                    experiment.name
                  }}</a>
                </TableCell>
                <TableCell v-if="applicationName(experiment)">
                  {{ applicationName(experiment) }}
                </TableCell>
                <TableCell v-else class="text-muted-foreground italic"
                  >N/A</TableCell
                >
                <TableCell>{{ experiment.user_name }}</TableCell>
                <TableCell>
                  <span :title="experiment.creation_time">{{
                    fromNow(experiment.creation_time)
                  }}</span>
                </TableCell>
                <TableCell>
                  <experiment-status-badge
                    :statusName="experiment.experiment_status.name"
                  />
                </TableCell>
                <TableCell>
                  <!-- if we can't load the application for the experiment
                  (for example, if it was deleted), then user can't edit or
                  clone experiment -->
                  <span v-if="applicationName(experiment)">
                    <a
                      v-if="
                        experiment.isEditable && applicationName(experiment)
                      "
                      :href="editLink(experiment)"
                      class="inline-flex items-center gap-1 text-primary"
                      >Edit
                      <Pencil class="size-4" aria-hidden="true" />
                    </a>
                    <a
                      v-else
                      href="#"
                      @click.prevent="clone(experiment)"
                      class="inline-flex items-center gap-1 text-primary"
                      >Clone
                      <Copy class="size-4" aria-hidden="true" />
                    </a>
                  </span>
                </TableCell>
              </TableRow>
            </TableBody>
          </Table>
          <pager
            v-bind:paginator="experimentsPaginator"
            v-on:next="nextExperiments"
            v-on:previous="previousExperiments"
          ></pager>
        </CardContent>
      </Card>
    </div>
  </main-layout>
</template>

<script>
import { CalendarDays, Copy, Pencil } from "@lucide/vue";
import { errors, models, services, utils } from "django-airavata-api";
import { components as comps } from "django-airavata-common-ui";
import FlatPickr from "vue-flatpickr-component";
import "flatpickr/dist/flatpickr.css";
import { NATIVE_SELECT_CLASS } from "../lib/utils";

import dayjs from "dayjs";
import relativeTime from "dayjs/plugin/relativeTime";
import urls from "../utils/urls";

dayjs.extend(relativeTime);

export default {
  props: ["initialExperimentsData"],
  name: "experiment-list-container",
  data() {
    return {
      experimentsPaginator: null,
      applicationInterfaces: {},
      search: null,
      applicationSelect: null,
      projectSelect: null,
      dateSelect: null,
      experimentAttributeSelect: null,
      experimentStatusSelect: null,
      appInterfaces: null,
      projectInterfaces: null,
      fromDate: null,
      toDate: null,
      applicationSelected: false,
      projectSelected: false,
      defaultOptionSelected: true,
      dateConfig: {
        mode: "range",
        wrap: true,
        dateFormat: "Y-m-d",
        maxDate: new Date().fp_incr(1),
      },
    };
  },
  components: {
    CalendarDays,
    Copy,
    Pencil,
    "main-layout": comps.MainLayout,
    pager: comps.Pager,
    "experiment-status-badge": comps.ExperimentStatusBadge,
    "flat-pickr": FlatPickr,
  },
  methods: {
    searchExperiments: function () {
      this.experimentsPaginator = null;
      this.reloadExperiments();
    },
    resetSearch: function () {
      this.experimentsPaginator = null;
      this.search = null;
      this.experimentAttributeSelect = null;
      this.experimentStatusSelect = null;
      this.applicationSelect = null;
      this.projectSelect = null;
      this.dateSelect = null;
      this.toDate = null;
      this.fromDate = null;
      this.checkSearchOptions();
      this.reloadExperiments();
    },
    reloadExperiments: function () {
      const searchParams = {};
      if (this.experimentAttributeSelect) {
        if (
          this.experimentAttributeSelect == "APPLICATION_ID" &&
          this.applicationSelect
        ) {
          searchParams["APPLICATION_ID"] = this.applicationSelect;
        } else if (
          this.experimentAttributeSelect == "PROJECT_ID" &&
          this.projectSelect
        ) {
          searchParams["PROJECT_ID"] = this.projectSelect;
        } else if (this.search) {
          searchParams[this.experimentAttributeSelect] = this.search;
        }
      }
      if (this.experimentStatusSelect) {
        if (this.experimentStatusSelect != "ALL") {
          searchParams["STATUS"] = this.experimentStatusSelect;
        }
      }
      if (this.fromDate && this.toDate) {
        searchParams["FROM_DATE"] = this.fromDate.getTime();
        searchParams["TO_DATE"] = this.toDate.getTime();
      }

      services.ExperimentSearchService.list(searchParams).then(
        (result) => (this.experimentsPaginator = result),
      );
    },
    checkSearchOptions: function () {
      this.applicationSelected = false;
      this.projectSelected = false;
      this.defaultOptionSelected = false;
      if (this.experimentAttributeSelect == "APPLICATION_ID") {
        this.applicationSelected = true;
      } else if (this.experimentAttributeSelect == "PROJECT_ID") {
        this.projectSelected = true;
      } else {
        this.defaultOptionSelected = true;
      }
    },
    loadApplicationInterfaces: function () {
      return services.ApplicationInterfaceService.list().then(
        (appInterfaces) => (this.appInterfaces = appInterfaces),
      );
    },
    loadProjectInterfaces: function () {
      return services.ProjectService.listAll().then(
        (projectInterfaces) => (this.projectInterfaces = projectInterfaces),
      );
    },
    dateRangeChanged: function (selectedDates) {
      [this.fromDate, this.toDate] = selectedDates;
      if (this.fromDate && this.toDate) {
        this.reloadExperiments();
      }
    },
    nextExperiments: function () {
      this.experimentsPaginator.next();
    },
    previousExperiments: function () {
      this.experimentsPaginator.previous();
    },
    fromNow: function (date) {
      return dayjs(date).fromNow();
    },
    editLink: function (experiment) {
      return urls.editExperiment(experiment);
    },
    viewLink: function (experiment) {
      return urls.viewExperiment(experiment);
    },
    applicationName: function (experiment) {
      if (experiment.execution_id in this.applicationInterfaces) {
        if (
          this.applicationInterfaces[experiment.execution_id] instanceof
          models.ApplicationInterfaceDefinition
        ) {
          return this.applicationInterfaces[experiment.execution_id]
            .application_name;
        } else if (
          this.applicationInterfaces[experiment.execution_id] === null
        ) {
          return null;
        }
      } else {
        const request = services.ApplicationInterfaceService.retrieve(
          {
            lookup: experiment.execution_id,
          },
          {
            ignoreErrors: true,
          },
        )
          .then((result) => {
            // Vue 3 reactivity is Proxy-based; plain assignment replaces $set.
            this.applicationInterfaces[experiment.execution_id] = result;
          })
          .catch((error) => {
            if (errors.ErrorUtils.isNotFoundError(error)) {
              this.applicationInterfaces[experiment.execution_id] = null;
            } else {
              throw error;
            }
          })
          .catch(utils.FetchUtils.reportError);
        this.applicationInterfaces[experiment.execution_id] = request;
      }
      return "...";
    },
    clone(experiment) {
      services.ExperimentService.clone({
        lookup: experiment.experiment_id,
      }).then((clonedExperiment) => {
        urls.navigateToEditExperiment(clonedExperiment);
      });
    },
  },
  computed: {
    selectClass() {
      // Native option-driven selects styled to match a shadcn <Input> (h-9), made
      // flexible so they share the filter toolbar row.
      return `${NATIVE_SELECT_CLASS} w-auto flex-1`;
    },
    experiments: function () {
      return this.experimentsPaginator
        ? this.experimentsPaginator.results
        : null;
    },
    applicationNameOptions() {
      if (this.appInterfaces) {
        const options = this.appInterfaces.map((appInterface) => {
          return {
            value: appInterface.application_interface_id,
            text: appInterface.application_name,
          };
        });
        return utils.StringUtils.sortIgnoreCase(options, (o) => o.text);
      } else {
        return [];
      }
    },
    projectNameOptions() {
      if (this.projectInterfaces) {
        const options = this.projectInterfaces.map((projectInterface) => {
          return {
            value: projectInterface.project_id,
            text: projectInterface.name,
          };
        });
        return utils.StringUtils.sortIgnoreCase(options, (o) => o.text);
      } else {
        return [];
      }
    },
  },
  beforeMount: function () {
    this.loadApplicationInterfaces();
    this.loadProjectInterfaces();
    services.ExperimentSearchService.list({
      initialData: this.initialExperimentsData,
    }).then((result) => (this.experimentsPaginator = result));
  },
};
</script>

<style></style>
