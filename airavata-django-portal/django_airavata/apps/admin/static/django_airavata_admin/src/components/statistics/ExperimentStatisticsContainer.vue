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
                <input class="form-control"
                  v-model.trim="experimentId"
                  placeholder="Experiment ID"
                  @keydown.enter="
                    experimentId && showExperimentDetails(experimentId)
                  "
                />
                <span class="input-group-text">
                  <button class="btn"
                    :disabled="!experimentId"
                    @click="showExperimentDetails(experimentId)"
                    >Load</button
                  >
                </span>
              </div>
            </div>
          </div>
        </li>
        <li class="nav-item" title="By Job ID">
          <div class="card-text">
            <div class="mb-3">
              <div class="input-group">
                <input class="form-control"
                  v-model.trim="jobId"
                  placeholder="Job ID"
                  @keydown.enter="
                    jobId && showExperimentDetailsForJobId(jobId)
                  "
                />
                <span class="input-group-text">
                  <button class="btn"
                    :disabled="!jobId"
                    @click="showExperimentDetailsForJobId(jobId)"
                    >Load</button
                  >
                </span>
              </div>
            </div>
          </div>
        </li>
      </ul>
    </div>
    <div class="card" no-body>
      <ul class="nav nav-tabs" ref="tabs">
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
                    @on-change="dateRangeChanged"
                    class="form-control"
                  />
                  <span class="input-group-text">
                    <button class="btn"
                      @click="getPast24Hours"
                      >Past 24 Hours</button
                    >
                    <button class="btn" @click="getPastWeek"
                      >Past Week</button
                    >
                  </span>
                </div>
                <div class="dropdown mb-2">
                  <a class="dropdown-item"
                    v-if="!usernameFilterEnabled"
                    @click="usernameFilterEnabled = true"
                    >Username</a
                  >
                  <a class="dropdown-item"
                    v-if="!applicationNameFilterEnabled"
                    @click="applicationNameFilterEnabled = true"
                    >Application Name</a
                  >
                  <a class="dropdown-item"
                    v-if="!hostnameFilterEnabled"
                    @click="hostnameFilterEnabled = true"
                    >Hostname</a
                  >
                </div>
                <div class="input-group mb-2" v-if="usernameFilterEnabled">
                  <input class="form-control"
                    v-model="usernameFilter"
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
                <div class="input-group mb-2" v-if="applicationNameFilterEnabled">
                  <select class="form-select"
                    v-model="applicationNameFilter"
                    :options="applicationNameOptions"
                    @input="loadStatistics"
                  >
                    <template slot="first">
                      <option :value="null" disabled>
                        Select an application to filter on
                      </option>
                    </template>
                  </select>
                  <span class="input-group-text">
                    <button class="btn" @click="removeApplicationNameFilter">
                      <i class="fa fa-times"></i>
                      <span class="visually-hidden"
                        >Remove application name filter</span
                      >
                    </button>
                  </span>
                </div>
                <div class="input-group mb-2" v-if="hostnameFilterEnabled">
                  <select class="form-select"
                    v-model="hostnameFilter"
                    :options="hostnameOptions"
                    @input="loadStatistics"
                  >
                    <template slot="first">
                      <option :value="null" disabled>
                        Select compute resource to filter on
                      </option>
                    </template>
                  </select>
                  <span class="input-group-text">
                    <button class="btn" @click="removeHostnameFilter">
                      <i class="fa fa-times"></i>
                      <span class="visually-hidden">Remove hostname filter</span>
                    </button>
                  </span>
                </div>
                <template slot="footer">
                  <div class="d-flex justify-content-end">
                    <button class="btn ms-auto"
                      @click="loadStatistics"
                      >Get Statistics</button
                    >
                  </div>
                </template>
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
                <span slot="link-text">All</span>
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
          <div class="row" v-if="items.length > 0">
            <div class="col">
              <div class="card">
                <div class="card-body">
                <!-- TODO: Replace b-table with native table -->
                <table class="table">
                  <tbody>
                    <tr v-for="item in items" :key="item.experiment_id">
                      <td><application-name :application-interface-id="item.execution_id" /></td>
                      <td><compute-resource-name :compute-resource-id="item.resource_host_id" /></td>
                      <td><human-date :date="item.creation_time" /></td>
                      <td><experiment-status-badge :status-name="item.experiment_status.name" /></td>
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
                v-if="experimentStatistics.allExperimentCount > 0"
                :paginator="experimentStatisticsPaginator"
                @next="experimentStatisticsPaginator.next()"
                @previous="experimentStatisticsPaginator.previous()"
              ></pager>
            </div>
          </div>
        </li>
        <li class="nav-item"
          v-for="experimentTab in experimentDetailTabs"
          :key="experimentTab.experiment.experiment_id"
        >
          <template slot="title">
            {{ experimentTab.tabTitle }}
            <a
              @click="
                removeExperimentDetailTab(experimentTab.experiment.experiment_id)
              "
              class="text-secondary"
            >
              <i class="fas fa-times"></i>
              <span class="visually-hidden">Close experiment tab</span>
            </a>
          </template>
          <experiment-details-view :experiment="experimentTab.experiment" />
        </li>
      </ul>
    </div>
  </div>
</template>
<script>
import { errors, models, services, utils } from "django-airavata-api";
import { components, notifications } from "django-airavata-common-ui";
import ExperimentStatisticsCard from "./ExperimentStatisticsCard";
import ExperimentDetailsView from "./ExperimentDetailsView";

import moment from "moment";

export default {
  name: "experiment-statistics-container",
  data() {
    //fp_incr sets the time of the date to midnight.
    //Calculating from today midnight to tomorrow midnight.
    const fromTime = new Date().fp_incr(0);
    const toTime = new Date().fp_incr(1);
    return {
      experimentStatisticsPaginator: null,
      selectedExperimentSummariesKey: null,
      fromTime: fromTime,
      toTime: toTime,
      dateRange: [fromTime, toTime],
      dateConfig: {
        mode: "range",
        wrap: true,
        dateFormat: "Y-m-d",
        maxDate: new Date().fp_incr(1),
      },
      usernameFilterEnabled: false,
      usernameFilter: null,
      applicationNameFilterEnabled: false,
      applicationNameFilter: null,
      hostnameFilterEnabled: false,
      hostnameFilter: null,
      appInterfaces: null,
      computeResourceNames: null,
      groupResourceProfiles: null,
      experimentDetailTabs: [],
      experimentId: null,
      jobId: null,
      activeTabIndex: 0,
    };
  },
  created() {
    this.loadStatistics();
    this.loadApplicationInterfaces();
    this.loadComputeResources();
    this.loadGroupResourceProfiles();
  },
  components: {
    ExperimentDetailsView,
    ExperimentStatisticsCard,
    "application-name": components.ApplicationName,
    "compute-resource-name": components.ComputeResourceName,
    "human-date": components.HumanDate,
    "experiment-status-badge": components.ExperimentStatusBadge,
    pager: components.Pager,
  },
  computed: {
    experimentStatistics() {
      return this.experimentStatisticsPaginator
        ? this.experimentStatisticsPaginator.results
        : {};
    },
    createdStates() {
      // TODO: moved to ExperimentStatistics model
      return [models.ExperimentState.CREATED, models.ExperimentState.VALIDATED];
    },
    runningStates() {
      return [
        models.ExperimentState.SCHEDULED,
        models.ExperimentState.LAUNCHED,
        models.ExperimentState.EXECUTING,
      ];
    },
    completedStates() {
      return [models.ExperimentState.COMPLETED];
    },
    canceledStates() {
      return [
        models.ExperimentState.CANCELING,
        models.ExperimentState.CANCELED,
      ];
    },
    failedStates() {
      return [models.ExperimentState.FAILED];
    },
    fields() {
      return [
        {
          key: "name",
          label: "Name",
        },
        {
          key: "user_name",
          label: "Owner",
        },
        {
          key: "execution_id",
          label: "Application",
        },
        {
          key: "resource_host_id",
          label: "Resource",
        },
        {
          key: "creation_time",
          label: "Creation Time",
        },
        {
          key: "experiment_status",
          label: "Status",
        },
        {
          key: "actions",
          label: "Actions",
        },
      ];
    },
    items() {
      if (this.selectedExperimentSummaries) {
        return this.selectedExperimentSummaries;
      } else {
        return [];
      }
    },
    fromTimeDisplay() {
      return moment(this.fromTime).format("MMM Do YYYY");
    },
    toTimeDisplay() {
      return moment(this.toTime).format("MMM Do YYYY");
    },
    selectedExperimentSummaries() {
      if (
        this.selectedExperimentSummariesKey &&
        this.experimentStatistics &&
        this.selectedExperimentSummariesKey in this.experimentStatistics
      ) {
        return this.experimentStatistics[this.selectedExperimentSummariesKey];
      } else {
        return [];
      }
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
    hostnameOptions() {
      if (this.computeResourceNames && this.groupResourceProfiles) {
        // Only show compute resources that are configured in the Group Resource Profiles
        // First create a Set of all compute resource ids in the GRPs
        const groupResourceProfileCompResources = new Set(
          this.groupResourceProfiles.flatMap((grp) =>
            grp.compute_preferences.map((cp) => cp.compute_resource_id)
          )
        );
        const options = this.computeResourceNames
          .filter((name) => groupResourceProfileCompResources.has(name.host_id))
          .map((name) => {
            return {
              value: name.host_id,
              text: name.host,
            };
          });
        return utils.StringUtils.sortIgnoreCase(options, (o) => o.text);
      } else {
        return [];
      }
    },
    selectedExperimentsTabTitle() {
      if (this.selectedExperimentSummariesKey === "allExperiments") {
        return "All Experiments";
      } else if (this.selectedExperimentSummariesKey === "createdExperiments") {
        return "Created Experiments";
      } else if (this.selectedExperimentSummariesKey === "runningExperiments") {
        return "Running Experiments";
      } else if (
        this.selectedExperimentSummariesKey === "completedExperiments"
      ) {
        return "Completed Experiments";
      } else if (
        this.selectedExperimentSummariesKey === "cancelledExperiments"
      ) {
        return "Cancelled Experiments";
      } else if (this.selectedExperimentSummariesKey === "failedExperiments") {
        return "Failed Experiments";
      } else {
        return "Experiments";
      }
    },
  },
  methods: {
    dateRangeChanged(selectedDates) {
      [this.fromTime, this.toTime] = selectedDates;
      if (this.fromTime && this.toTime) {
        this.loadStatistics();
      }
    },
    loadApplicationInterfaces() {
      return services.ApplicationInterfaceService.list().then(
        (appInterfaces) => (this.appInterfaces = appInterfaces)
      );
    },
    loadComputeResources() {
      return services.ComputeResourceService.namesList().then(
        (names) => (this.computeResourceNames = names)
      );
    },
    async loadGroupResourceProfiles() {
      this.groupResourceProfiles = await services.GroupResourceProfileService.list();
    },
    loadStatistics() {
      const requestData = {
        fromTime: this.fromTime.toJSON(),
        toTime: this.toTime.toJSON(),
      };
      if (this.usernameFilterEnabled && this.usernameFilter) {
        requestData["user_name"] = this.usernameFilter;
      }
      if (this.applicationNameFilterEnabled && this.applicationNameFilter) {
        requestData["application_name"] = this.applicationNameFilter;
      }
      if (this.hostnameFilterEnabled && this.hostnameFilter) {
        requestData["resource_host_name"] = this.hostnameFilter;
      }
      return services.ExperimentStatisticsService.get(requestData).then(
        (stats) => {
          this.experimentStatisticsPaginator = stats;
        }
      );
    },
    getPast24Hours() {
      this.fromTime = new Date().fp_incr(0);
      //this.fromTime = new Date(this.fromTime.setHours(0,0,0));
      this.toTime = new Date().fp_incr(1);
      this.updateDateRange();
    },
    getPastWeek() {
      this.fromTime = new Date().fp_incr(-7);
      this.toTime = new Date().fp_incr(1);
      this.updateDateRange();
    },
    updateDateRange() {
      this.dateRange = [
        moment(this.fromTime).format("YYYY-MM-DD"),
        moment(this.toTime).format("YYYY-MM-DD"),
      ];
    },
    daysAgo(days) {
      return new Date(Date.now() - days * 24 * 60 * 60 * 1000);
    },
    removeUsernameFilter() {
      this.usernameFilter = null;
      this.usernameFilterEnabled = false;
      this.loadStatistics();
    },
    removeApplicationNameFilter() {
      this.applicationNameFilter = null;
      this.applicationNameFilterEnabled = false;
      this.loadStatistics();
    },
    removeHostnameFilter() {
      this.hostnameFilter = null;
      this.hostnameFilterEnabled = false;
      this.loadStatistics();
    },
    async showExperimentDetails(experimentId, tabTitle = null) {
      const expDetailsIndex = this.getExperimentDetailTabsIndex(experimentId);
      if (expDetailsIndex >= 0) {
        // Update tab title in case it is now loaded from a job id and we want
        // to get the job id in the title
        if (tabTitle) {
          this.experimentDetailTabs[expDetailsIndex].tabTitle = tabTitle;
        }
        this.selectExperimentDetailsTab(experimentId);
      } else {
        try {
          const exp = await services.ExperimentService.retrieve(
            {
              lookup: experimentId,
            },
            { ignoreErrors: true }
          );
          this.experimentDetailTabs.push({
            tabTitle: tabTitle || exp.experiment_name,
            experiment: exp,
          });
          this.selectExperimentDetailsTab(experimentId);
          this.scrollTabsIntoView();
        } catch (error) {
          if (errors.ErrorUtils.isNotFoundError(error)) {
            notifications.NotificationList.add(
              new notifications.Notification({
                type: "WARNING",
                message: `No experiment exists with experiment id ${experimentId}`,
                duration: 5,
              })
            );
          } else {
            utils.FetchUtils.reportError(error);
          }
        }
      }
    },
    async showExperimentDetailsForJobId(jobId) {
      const searchResults = await services.ExperimentSearchService.list({
        [models.ExperimentSearchFields.JOB_ID.name]: jobId,
      });
      if (searchResults.results.length === 0) {
        notifications.NotificationList.add(
          new notifications.Notification({
            type: "WARNING",
            message: `No experiment exists with job id ${jobId}`,
            duration: 5,
          })
        );
      } else {
        if (searchResults.results.length > 1) {
          notifications.NotificationList.add(
            new notifications.Notification({
              type: "WARNING",
              message: `More than one experiment matches job id ${jobId}, showing the latest one`,
              duration: 5,
            })
          );
        }
        this.showExperimentDetails(
          searchResults.results[0].experiment_id,
          `Job ${jobId}`
        );
      }
    },
    selectExperimentDetailsTab(experimentId) {
      const expDetailsIndex = this.getExperimentDetailTabsIndex(experimentId);
      // Note: running this in $nextTick doesn't work, but setTimeout does
      // (see also https://github.com/bootstrap-vue/bootstrap-vue/issues/1378#issuecomment-345689470)
      setTimeout(() => {
        // Add 1 to the index because the first tab has the overall statistics
        this.activeTabIndex = expDetailsIndex + 1;
      }, 1);
    },
    getExperimentDetailTabsIndex(experimentId) {
      return this.experimentDetailTabs.findIndex(
        (tab) => tab.experiment.experiment_id === experimentId
      );
    },
    removeExperimentDetailTab(experimentId) {
      const index = this.getExperimentDetailTabsIndex(experimentId);
      this.experimentDetailTabs.splice(index, 1);
    },
    scrollTabsIntoView() {
      this.$refs.tabs.$el.scrollIntoView({ behavior: "smooth" });
    },
    selectExperiments(experimentSummariesKey) {
      if (
        this.experimentStatisticsPaginator &&
        this.experimentStatisticsPaginator.offset > 0
      ) {
        this.loadStatistics();
      }
      this.selectedExperimentSummariesKey = experimentSummariesKey;
    },
  },
};
</script>
