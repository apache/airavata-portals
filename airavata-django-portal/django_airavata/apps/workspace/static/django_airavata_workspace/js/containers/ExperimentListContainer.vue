<template>
  <div>
    <breadcrumb-nav :crumbs="breadcrumbs" />
    <div class="row align-items-center mb-3">
      <div class="col">
        <h1 class="h4 mb-0">Experiments</h1>
        <p class="text-muted mb-0">Search, view, and manage your computational experiments.</p>
      </div>
      <div class="col-auto">
        <a href="/workspace/applications" class="btn btn-primary btn-sm"
          ><i class="fa fa-plus me-1"></i>Create New</a
        >
      </div>
    </div>
    <div class="mb-3">
      <div class="d-flex align-items-center gap-2 flex-wrap">
        <div class="input-group input-group-sm" style="flex: 1 1 300px; max-width: 420px">
          <select
            v-model="experimentAttributeSelect"
            class="form-select"
            style="flex: 0 0 auto; width: auto; min-width: 110px"
            @change="checkSearchOptions"
          >
            <option :value="null" disabled>Attribute</option>
            <option value="USER_NAME">User</option>
            <option value="EXPERIMENT_NAME">Name</option>
            <option value="EXPERIMENT_DESC">Description</option>
            <option value="APPLICATION_ID">Application</option>
            <option value="JOB_ID">Job ID</option>
          </select>
          <input
            v-if="defaultOptionSelected"
            v-model="search"
            class="form-control"
            placeholder="Search..."
            @keydown.enter="searchExperiments"
          />
          <select v-if="applicationSelected" v-model="applicationSelect" class="form-select">
            <option :value="null" disabled>Select application</option>
            <option v-for="opt in applicationNameOptions" :key="opt.value" :value="opt.value">
              {{ opt.text }}
            </option>
          </select>
        </div>
        <select
          v-model="experimentStatusSelect"
          class="form-select form-select-sm"
          style="width: auto; min-width: 100px"
        >
          <option :value="null" disabled>Status</option>
          <option value="ALL">All</option>
          <option value="CREATED">Created</option>
          <option value="VALIDATED">Validated</option>
          <option value="SCHEDULED">Scheduled</option>
          <option value="LAUNCHED">Launched</option>
          <option value="EXECUTING">Executing</option>
          <option value="CANCELED">Canceled</option>
          <option value="COMPLETED">Completed</option>
          <option value="FAILED">Failed</option>
        </select>
        <div style="width: 180px">
          <flat-pickr
            v-model="dateSelect"
            :config="dateConfig"
            placeholder="Date range"
            class="form-control form-control-sm"
            @on-change="dateRangeChanged"
          />
        </div>
        <button class="btn btn-outline-secondary btn-sm" @click="resetSearch">Reset</button>
        <button class="btn btn-primary btn-sm" @click="searchExperiments">
          <i class="fa fa-search me-1"></i>Search
        </button>
      </div>
    </div>
    <div class="card">
      <div class="card-body">
        <table class="table table-hover table-sm">
          <thead>
            <tr>
              <th>Name</th>
              <th class="text-nowrap">Application</th>
              <th class="text-nowrap">User</th>
              <th class="text-nowrap">Creation Time</th>
              <th class="text-nowrap">Status</th>
              <th class="text-nowrap" style="width: 1%">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="!experiments || experiments.length === 0">
              <td colspan="6">
                <div class="table-empty">
                  <i class="fa fa-flask table-empty__icon"></i>
                  <div class="table-empty__title">No experiments yet</div>
                  <div class="table-empty__text">
                    Launch your first experiment from the
                    <a href="/workspace/applications">Dashboard</a>.
                  </div>
                </div>
              </td>
            </tr>
            <tr v-for="experiment in experiments || []" :key="experiment.experiment_id">
              <td>
                <a :href="viewLink(experiment)">{{ experiment.name }}</a>
              </td>
              <td v-if="applicationName(experiment)">{{ applicationName(experiment) }}</td>
              <td v-else class="text-muted">N/A</td>
              <td>{{ experiment.user_name }}</td>
              <td>
                <span :title="experiment.creation_time">{{
                  fromNow(experiment.creation_time)
                }}</span>
              </td>
              <td><experiment-status-badge :status-name="experiment.experiment_status.name" /></td>
              <td class="text-nowrap" style="width: 1%">
                <div
                  v-if="applicationName(experiment)"
                  class="d-flex gap-2 justify-content-end flex-nowrap"
                >
                  <a
                    v-if="experiment.isEditable"
                    :href="editLink(experiment)"
                    class="btn btn-sm btn-outline-primary"
                    ><i class="fa fa-edit me-1"></i>Edit</a
                  >
                  <button
                    v-else
                    type="button"
                    class="btn btn-sm btn-outline-primary"
                    @click="clone(experiment)"
                  >
                    <i class="fa fa-copy me-1"></i>Clone
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
        <pager
          v-if="experiments && experiments.length > 0"
          :paginator="experimentsPaginator"
          @next="nextExperiments"
          @previous="previousExperiments"
        ></pager>
      </div>
    </div>
  </div>
</template>

<script>
import { errors, models, services, utils } from "django-airavata-api";
import { components as comps } from "django-airavata-common-ui";
import flatPickr from "vue-flatpickr-component";
import "flatpickr/dist/flatpickr.css";

import moment from "moment";
import urls from "../utils/urls";

export default {
  name: "ExperimentListContainer",
  components: {
    pager: comps.Pager,
    "experiment-status-badge": comps.ExperimentStatusBadge,
    "breadcrumb-nav": comps.BreadcrumbNav,
    flatPickr,
  },
  props: {
    initialExperimentsData: { default: null },
    projectId: { type: String, default: null },
    breadcrumbs: { type: Array, default: () => [] },
  },
  data() {
    return {
      experimentsPaginator: null,
      applicationInterfaces: {},
      search: null,
      applicationSelect: null,
      dateSelect: null,
      experimentAttributeSelect: null,
      experimentStatusSelect: null,
      appInterfaces: null,
      fromDate: null,
      toDate: null,
      applicationSelected: false,
      defaultOptionSelected: true,
      dateConfig: {
        mode: "range",
        wrap: true,
        dateFormat: "Y-m-d",
        maxDate: new Date(Date.now() + 86400000),
      },
    };
  },
  computed: {
    experiments: function () {
      return this.experimentsPaginator ? this.experimentsPaginator.results : null;
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
  },
  beforeMount: function () {
    this.loadApplicationInterfaces();
    services.ExperimentSearchService.list({
      initialData: this.initialExperimentsData,
    }).then((result) => (this.experimentsPaginator = result));
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
      this.dateSelect = null;
      this.toDate = null;
      this.fromDate = null;
      this.checkSearchOptions();
      this.reloadExperiments();
    },
    reloadExperiments: function () {
      const searchParams = {};
      if (this.projectId) {
        searchParams["PROJECT_ID"] = this.projectId;
      }
      if (this.experimentAttributeSelect) {
        if (this.experimentAttributeSelect === "APPLICATION_ID" && this.applicationSelect) {
          searchParams["APPLICATION_ID"] = this.applicationSelect;
        } else if (this.search) {
          searchParams[this.experimentAttributeSelect] = this.search;
        }
      }
      if (this.experimentStatusSelect) {
        if (this.experimentStatusSelect !== "ALL") {
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
      this.defaultOptionSelected = false;
      if (this.experimentAttributeSelect === "APPLICATION_ID") {
        this.applicationSelected = true;
      } else {
        this.defaultOptionSelected = true;
      }
    },
    loadApplicationInterfaces: function () {
      return services.ApplicationInterfaceService.list().then(
        (appInterfaces) => (this.appInterfaces = appInterfaces),
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
      return moment(date).fromNow();
    },
    editLink: function (experiment) {
      return urls.editExperiment(this.projectId, experiment);
    },
    viewLink: function (experiment) {
      return urls.viewExperiment(this.projectId, experiment);
    },
    applicationName: function (experiment) {
      if (experiment.execution_id in this.applicationInterfaces) {
        if (
          this.applicationInterfaces[experiment.execution_id] instanceof
          models.ApplicationInterfaceDefinition
        ) {
          return this.applicationInterfaces[experiment.execution_id].application_name;
        } else if (this.applicationInterfaces[experiment.execution_id] === null) {
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
            this.$set(this.applicationInterfaces, experiment.execution_id, result);
          })
          .catch((error) => {
            if (errors.ErrorUtils.isNotFoundError(error)) {
              this.$set(this.applicationInterfaces, experiment.execution_id, null);
            } else {
              throw error;
            }
          })
          .catch(utils.FetchUtils.reportError);
        this.$set(this.applicationInterfaces, experiment.execution_id, request);
      }
      return "...";
    },
    clone(experiment) {
      services.ExperimentService.clone({
        lookup: experiment.experiment_id,
      }).then((clonedExperiment) => {
        urls.navigateToEditExperiment(this.projectId, clonedExperiment);
      });
    },
  },
};
</script>

<style></style>
