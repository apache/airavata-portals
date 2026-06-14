<template>
  <main-layout
    title="Experiment Statistics"
    subtitle="Browse experiment activity and details across the gateway."
  >
    <div class="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>Load experiment details</CardTitle>
        </CardHeader>
        <CardContent>
          <Tabs default-value="by-experiment-id">
            <TabsList>
              <TabsTrigger value="by-experiment-id"
                >By Experiment ID</TabsTrigger
              >
              <TabsTrigger value="by-job-id">By Job ID</TabsTrigger>
            </TabsList>
            <TabsContent value="by-experiment-id" class="pt-4">
              <div class="flex items-stretch gap-2">
                <Input
                  v-model.trim="experimentId"
                  placeholder="Experiment ID"
                  @keydown.enter="
                    experimentId && showExperimentDetails(experimentId)
                  "
                />
                <Button
                  :disabled="!experimentId"
                  @click="showExperimentDetails(experimentId)"
                  variant="default"
                  >Load</Button
                >
              </div>
            </TabsContent>
            <TabsContent value="by-job-id" class="pt-4">
              <div class="flex items-stretch gap-2">
                <Input
                  v-model.trim="jobId"
                  placeholder="Job ID"
                  @keydown.enter="jobId && showExperimentDetailsForJobId(jobId)"
                />
                <Button
                  :disabled="!jobId"
                  @click="showExperimentDetailsForJobId(jobId)"
                  variant="default"
                  >Load</Button
                >
              </div>
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
      <Card>
        <CardContent>
          <Tabs v-model="activeTab" ref="tabs">
            <TabsList>
              <TabsTrigger value="statistics">{{
                selectedExperimentsTabTitle
              }}</TabsTrigger>
              <TabsTrigger
                v-for="experimentTab in experimentDetailTabs"
                :key="experimentTab.experiment.experiment_id"
                :value="experimentTab.experiment.experiment_id"
              >
                {{ experimentTab.tabTitle }}
                <a
                  href="#"
                  @click.prevent="
                    removeExperimentDetailTab(
                      experimentTab.experiment.experiment_id,
                    )
                  "
                  class="text-muted-foreground ml-1"
                >
                  <X class="size-3.5" />
                  <span class="sr-only">Close experiment tab</span>
                </a>
              </TabsTrigger>
            </TabsList>
            <TabsContent value="statistics" class="space-y-4 pt-4">
              <Card>
                <CardHeader>
                  <CardTitle>Filter Options</CardTitle>
                </CardHeader>
                <CardContent>
                  <div class="mb-2 flex w-full items-stretch gap-2">
                    <span
                      class="border-input flex items-center rounded-md border px-3"
                    >
                      <CalendarDays class="size-4" aria-hidden="true" />
                    </span>
                    <flat-pickr
                      :value="dateRange"
                      :config="dateConfig"
                      @on-change="dateRangeChanged"
                      class="border-input focus-visible:border-ring focus-visible:ring-ring/50 h-9 flex-1 rounded-md border bg-transparent px-3 py-1 text-sm shadow-xs outline-none focus-visible:ring-3"
                    />
                    <Button @click="getPast24Hours" variant="outline"
                      >Past 24 Hours</Button
                    >
                    <Button @click="getPastWeek" variant="outline"
                      >Past Week</Button
                    >
                  </div>
                  <DropdownMenu>
                    <DropdownMenuTrigger as-child>
                      <Button variant="outline" class="mb-2"
                        >Add Filters</Button
                      >
                    </DropdownMenuTrigger>
                    <DropdownMenuContent>
                      <DropdownMenuItem
                        v-if="!usernameFilterEnabled"
                        @click="usernameFilterEnabled = true"
                        >Username</DropdownMenuItem
                      >
                      <DropdownMenuItem
                        v-if="!applicationNameFilterEnabled"
                        @click="applicationNameFilterEnabled = true"
                        >Application Name</DropdownMenuItem
                      >
                      <DropdownMenuItem
                        v-if="!hostnameFilterEnabled"
                        @click="hostnameFilterEnabled = true"
                        >Hostname</DropdownMenuItem
                      >
                    </DropdownMenuContent>
                  </DropdownMenu>
                  <div
                    v-if="usernameFilterEnabled"
                    class="mb-2 flex items-stretch gap-2"
                  >
                    <Input
                      v-model="usernameFilter"
                      placeholder="Username"
                      @keydown.enter="loadStatistics"
                    />
                    <Button variant="outline" @click="removeUsernameFilter">
                      <X class="size-4" />
                      <span class="sr-only">Remove username filter</span>
                    </Button>
                  </div>
                  <div
                    v-if="applicationNameFilterEnabled"
                    class="mb-2 flex items-stretch gap-2"
                  >
                    <select
                      v-model="applicationNameFilter"
                      @change="loadStatistics"
                      class="border-input focus-visible:border-ring focus-visible:ring-ring/50 h-9 flex-1 rounded-md border bg-transparent px-3 py-1 text-sm shadow-xs outline-none focus-visible:ring-3"
                    >
                      <option :value="null" disabled>
                        Select an application to filter on
                      </option>
                      <option
                        v-for="opt in applicationNameOptions"
                        :key="opt.value"
                        :value="opt.value"
                      >
                        {{ opt.text }}
                      </option>
                    </select>
                    <Button
                      variant="outline"
                      @click="removeApplicationNameFilter"
                    >
                      <X class="size-4" />
                      <span class="sr-only"
                        >Remove application name filter</span
                      >
                    </Button>
                  </div>
                  <div
                    v-if="hostnameFilterEnabled"
                    class="mb-2 flex items-stretch gap-2"
                  >
                    <select
                      v-model="hostnameFilter"
                      @change="loadStatistics"
                      class="border-input focus-visible:border-ring focus-visible:ring-ring/50 h-9 flex-1 rounded-md border bg-transparent px-3 py-1 text-sm shadow-xs outline-none focus-visible:ring-3"
                    >
                      <option :value="null" disabled>
                        Select compute resource to filter on
                      </option>
                      <option
                        v-for="opt in hostnameOptions"
                        :key="opt.value"
                        :value="opt.value"
                      >
                        {{ opt.text }}
                      </option>
                    </select>
                    <Button variant="outline" @click="removeHostnameFilter">
                      <X class="size-4" />
                      <span class="sr-only">Remove hostname filter</span>
                    </Button>
                  </div>
                </CardContent>
                <CardFooter>
                  <div class="flex w-full justify-end">
                    <Button @click="loadStatistics" class="ml-auto"
                      >Get Statistics</Button
                    >
                  </div>
                </CardFooter>
              </Card>
              <div>
                <h2 class="mb-4 text-lg font-semibold">
                  Experiment Statistics from {{ fromTimeDisplay }} to
                  {{ toTimeDisplay }}
                </h2>
              </div>
              <div class="grid grid-cols-2 gap-4 md:grid-cols-3 xl:grid-cols-6">
                <experiment-statistics-card
                  :count="experimentStatistics.all_experiment_count || 0"
                  title="Total Experiments"
                  @click="selectExperiments('all_experiments')"
                >
                  <template v-slot:link-text>
                    <span>All</span>
                  </template>
                </experiment-statistics-card>
                <experiment-statistics-card
                  :count="experimentStatistics.created_experiment_count || 0"
                  :states="createdStates"
                  title="Created Experiments"
                  @click="selectExperiments('created_experiments')"
                >
                </experiment-statistics-card>
                <experiment-statistics-card
                  :count="experimentStatistics.running_experiment_count || 0"
                  :states="runningStates"
                  title="Running Experiments"
                  @click="selectExperiments('running_experiments')"
                >
                </experiment-statistics-card>
                <experiment-statistics-card
                  :count="experimentStatistics.completed_experiment_count || 0"
                  :states="completedStates"
                  title="Completed Experiments"
                  @click="selectExperiments('completed_experiments')"
                >
                </experiment-statistics-card>
                <experiment-statistics-card
                  :count="experimentStatistics.cancelled_experiment_count || 0"
                  :states="canceledStates"
                  title="Cancelled Experiments"
                  @click="selectExperiments('cancelled_experiments')"
                >
                </experiment-statistics-card>
                <experiment-statistics-card
                  :count="experimentStatistics.failed_experiment_count || 0"
                  :states="failedStates"
                  title="Failed Experiments"
                  @click="selectExperiments('failed_experiments')"
                >
                </experiment-statistics-card>
              </div>
              <div v-if="items.length > 0">
                <Card>
                  <CardContent>
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead v-for="field in fields" :key="field.key">
                            {{ field.label }}
                          </TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        <TableRow
                          v-for="item in items"
                          :key="item.experiment_id"
                        >
                          <TableCell>{{ item.name }}</TableCell>
                          <TableCell>{{ item.user_name }}</TableCell>
                          <TableCell>
                            <application-name
                              :application-interface-id="item.execution_id"
                            />
                          </TableCell>
                          <TableCell>
                            <compute-resource-name
                              :compute-resource-id="item.resource_host_id"
                            />
                          </TableCell>
                          <TableCell
                            ><human-date :date="item.creation_time"
                          /></TableCell>
                          <TableCell>
                            <experiment-status-badge
                              :status-name="item.experiment_status.name"
                            />
                          </TableCell>
                          <TableCell>
                            <a
                              href="#"
                              class="inline-flex items-center gap-1 text-primary hover:underline"
                              @click.prevent="
                                showExperimentDetails(item.experiment_id)
                              "
                            >
                              View Details
                              <BarChart3 class="size-4" aria-hidden="true" />
                            </a>
                          </TableCell>
                        </TableRow>
                      </TableBody>
                    </Table>
                  </CardContent>
                </Card>
                <pager
                  v-if="experimentStatistics.all_experiment_count > 0"
                  :paginator="experimentStatisticsPaginator"
                  @next="experimentStatisticsPaginator.next()"
                  @previous="experimentStatisticsPaginator.previous()"
                ></pager>
              </div>
            </TabsContent>
            <TabsContent
              v-for="experimentTab in experimentDetailTabs"
              :key="experimentTab.experiment.experiment_id"
              :value="experimentTab.experiment.experiment_id"
              class="pt-4"
            >
              <experiment-details-view :experiment="experimentTab.experiment" />
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  </main-layout>
</template>
<script>
import { BarChart3, CalendarDays, X } from "@lucide/vue";
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
      activeTab: "statistics",
    };
  },
  created() {
    this.loadStatistics();
    this.loadApplicationInterfaces();
    this.loadComputeResources();
    this.loadGroupResourceProfiles();
  },
  components: {
    BarChart3,
    CalendarDays,
    X,
    ExperimentDetailsView,
    ExperimentStatisticsCard,
    "application-name": components.ApplicationName,
    "compute-resource-name": components.ComputeResourceName,
    "human-date": components.HumanDate,
    "experiment-status-badge": components.ExperimentStatusBadge,
    "main-layout": components.MainLayout,
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
            grp.compute_preferences.map((cp) => cp.compute_resource_id),
          ),
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
      if (this.selectedExperimentSummariesKey === "all_experiments") {
        return "All Experiments";
      } else if (
        this.selectedExperimentSummariesKey === "created_experiments"
      ) {
        return "Created Experiments";
      } else if (
        this.selectedExperimentSummariesKey === "running_experiments"
      ) {
        return "Running Experiments";
      } else if (
        this.selectedExperimentSummariesKey === "completed_experiments"
      ) {
        return "Completed Experiments";
      } else if (
        this.selectedExperimentSummariesKey === "cancelled_experiments"
      ) {
        return "Cancelled Experiments";
      } else if (this.selectedExperimentSummariesKey === "failed_experiments") {
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
        (appInterfaces) => (this.appInterfaces = appInterfaces),
      );
    },
    loadComputeResources() {
      return services.ComputeResourceService.namesList().then(
        (names) => (this.computeResourceNames = names),
      );
    },
    async loadGroupResourceProfiles() {
      this.groupResourceProfiles =
        await services.GroupResourceProfileService.list();
    },
    loadStatistics() {
      const requestData = {
        fromTime: this.fromTime.toJSON(),
        toTime: this.toTime.toJSON(),
      };
      if (this.usernameFilterEnabled && this.usernameFilter) {
        requestData["userName"] = this.usernameFilter;
      }
      if (this.applicationNameFilterEnabled && this.applicationNameFilter) {
        requestData["applicationName"] = this.applicationNameFilter;
      }
      if (this.hostnameFilterEnabled && this.hostnameFilter) {
        requestData["resourceHostName"] = this.hostnameFilter;
      }
      return services.ExperimentStatisticsService.get(requestData).then(
        (stats) => {
          this.experimentStatisticsPaginator = stats;
        },
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
            { ignoreErrors: true },
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
              }),
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
          }),
        );
      } else {
        if (searchResults.results.length > 1) {
          notifications.NotificationList.add(
            new notifications.Notification({
              type: "WARNING",
              message: `More than one experiment matches job id ${jobId}, showing the latest one`,
              duration: 5,
            }),
          );
        }
        this.showExperimentDetails(
          searchResults.results[0].experiment_id,
          `Job ${jobId}`,
        );
      }
    },
    selectExperimentDetailsTab(experimentId) {
      // The shadcn Tabs are keyed by value; the per-experiment tabs use the
      // experiment id as their value. Defer a tick so the new tab is mounted
      // before we activate it.
      setTimeout(() => {
        this.activeTab = experimentId;
      }, 1);
    },
    getExperimentDetailTabsIndex(experimentId) {
      return this.experimentDetailTabs.findIndex(
        (tab) => tab.experiment.experiment_id === experimentId,
      );
    },
    removeExperimentDetailTab(experimentId) {
      const index = this.getExperimentDetailTabsIndex(experimentId);
      this.experimentDetailTabs.splice(index, 1);
      if (this.activeTab === experimentId) {
        this.activeTab = "statistics";
      }
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
