<template>
  <main-layout
    title="Experiment Statistics"
    subtitle="Gateway experiment activity over time."
  >
    <Tabs v-model="activeTab" ref="tabs" class="space-y-4">
      <!-- Only show the tab bar once experiment-detail tabs are open; the lone
           "Statistics" pill was a no-op (the statistics view is the default). -->
      <TabsList v-if="experimentDetailTabs.length > 0">
        <TabsTrigger
          v-for="experimentTab in experimentDetailTabs"
          :key="experimentTab.experiment.experiment_id"
          :value="experimentTab.experiment.experiment_id"
        >
          {{ experimentTab.tabTitle }}
          <a
            href="#"
            @click.prevent="
              removeExperimentDetailTab(experimentTab.experiment.experiment_id)
            "
            class="text-muted-foreground ml-1"
          >
            <X class="size-3.5" />
            <span class="sr-only">Close experiment tab</span>
          </a>
        </TabsTrigger>
      </TabsList>

      <TabsContent value="statistics" class="space-y-4">
        <!-- Primary deliverable: the time-series graph with an inline filter
             bar (date range + shortcuts + optional scoping filters). -->
        <Card>
          <CardContent class="space-y-4 pt-6">
            <div class="flex flex-wrap items-center justify-between gap-3">
              <div class="flex flex-wrap items-center gap-2">
                <span
                  class="border-input flex items-center rounded-md border px-3"
                >
                  <CalendarDays class="size-4" aria-hidden="true" />
                </span>
                <flat-pickr
                  v-model="dateRange"
                  :config="dateConfig"
                  @on-change="dateRangeChanged"
                  placeholder="Select a date range"
                  class="border-input focus-visible:border-ring focus-visible:ring-ring/50 h-9 w-56 rounded-md border bg-transparent px-3 py-1 text-sm shadow-xs outline-none focus-visible:ring-3"
                />
                <Button
                  v-for="shortcut in rangeShortcuts"
                  :key="shortcut.key"
                  :variant="
                    activeShortcut === shortcut.key ? 'default' : 'outline'
                  "
                  size="sm"
                  @click="applyShortcut(shortcut.key)"
                  >{{ shortcut.label }}</Button
                >
              </div>
              <div class="flex flex-wrap items-center gap-2">
                <DropdownMenu>
                  <DropdownMenuTrigger as-child>
                    <Button variant="outline" size="sm">
                      <FilterIcon class="size-4" />
                      Add filter
                    </Button>
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
                    <DropdownMenuItem
                      v-if="allFiltersEnabled"
                      disabled
                      class="text-muted-foreground"
                      >No more filters</DropdownMenuItem
                    >
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>
            </div>

            <!-- Active scoping filters, shown inline only when enabled. -->
            <div
              v-if="anyFilterEnabled"
              class="flex flex-wrap items-center gap-2"
            >
              <div
                v-if="usernameFilterEnabled"
                class="flex items-stretch gap-1"
              >
                <Input
                  v-model="usernameFilter"
                  placeholder="Username"
                  class="h-9 w-48"
                  @keydown.enter="loadStatistics"
                />
                <Button
                  variant="outline"
                  size="icon"
                  @click="removeUsernameFilter"
                >
                  <X class="size-4" />
                  <span class="sr-only">Remove username filter</span>
                </Button>
              </div>
              <div
                v-if="applicationNameFilterEnabled"
                class="flex items-stretch gap-1"
              >
                <select
                  v-model="applicationNameFilter"
                  @change="loadStatistics"
                  class="border-input focus-visible:border-ring focus-visible:ring-ring/50 h-9 w-56 rounded-md border bg-transparent px-3 py-1 text-sm shadow-xs outline-none focus-visible:ring-3"
                >
                  <option :value="null" disabled>Application name</option>
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
                  size="icon"
                  @click="removeApplicationNameFilter"
                >
                  <X class="size-4" />
                  <span class="sr-only">Remove application name filter</span>
                </Button>
              </div>
              <div
                v-if="hostnameFilterEnabled"
                class="flex items-stretch gap-1"
              >
                <select
                  v-model="hostnameFilter"
                  @change="loadStatistics"
                  class="border-input focus-visible:border-ring focus-visible:ring-ring/50 h-9 w-56 rounded-md border bg-transparent px-3 py-1 text-sm shadow-xs outline-none focus-visible:ring-3"
                >
                  <option :value="null" disabled>Compute resource</option>
                  <option
                    v-for="opt in hostnameOptions"
                    :key="opt.value"
                    :value="opt.value"
                  >
                    {{ opt.text }}
                  </option>
                </select>
                <Button
                  variant="outline"
                  size="icon"
                  @click="removeHostnameFilter"
                >
                  <X class="size-4" />
                  <span class="sr-only">Remove hostname filter</span>
                </Button>
              </div>
            </div>

            <!-- Compact, smooth-curved area chart (shadcn-vue AreaChart, built
                 on @unovis). A loading overlay covers it while the per-bucket
                 requests are in flight. The chart's own legend is disabled in
                 favor of the independent on/off toggle row below. -->
            <div class="relative h-64 w-full">
              <div
                v-if="loading"
                class="absolute inset-0 z-10 flex items-center justify-center bg-background/60"
              >
                <Loader2 class="size-6 animate-spin text-muted-foreground" />
              </div>
              <area-chart
                v-if="visibleCategories.length > 0 && chartData.length > 0"
                :key="chartKey"
                :data="chartData"
                :categories="visibleCategories"
                index="label"
                :colors="visibleColors"
                :curve-type="curveType"
                :y-formatter="formatCount"
                :show-legend="false"
                :show-grid-line="true"
                class="h-full"
              />
              <div
                v-else
                class="flex h-full items-center justify-center text-sm text-muted-foreground"
              >
                {{
                  chartData.length === 0
                    ? "No data for the selected range."
                    : "No series selected."
                }}
              </div>
            </div>
            <!-- Legend doubling as independent on/off toggles, in the series
                 colors, sized to the design-system text scale. -->
            <div class="flex flex-wrap gap-x-4 gap-y-2">
              <button
                v-for="s in series"
                :key="s.key"
                type="button"
                class="flex items-center gap-2 text-sm transition-opacity"
                :class="s.visible ? 'opacity-100' : 'opacity-40'"
                :aria-pressed="s.visible"
                @click="toggleSeries(s.key)"
              >
                <span
                  class="inline-block h-0.5 w-4 rounded-full"
                  :style="{ backgroundColor: s.color }"
                />
                <span>{{ s.label }}</span>
                <span class="text-muted-foreground tabular-nums">{{
                  s.total
                }}</span>
              </button>
            </div>
            <p class="text-xs text-muted-foreground">
              {{ rangeSummary }}
            </p>
          </CardContent>
        </Card>

        <!-- Secondary "find" affordances: a compact lookup and a drill-down
             experiments list for the selected status. -->
        <div class="grid gap-4 lg:grid-cols-3">
          <Card class="lg:col-span-1">
            <CardHeader>
              <CardTitle class="text-base">Find an experiment</CardTitle>
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
                      @keydown.enter="
                        jobId && showExperimentDetailsForJobId(jobId)
                      "
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

          <Card class="lg:col-span-2">
            <CardHeader class="flex-row items-center justify-between space-y-0">
              <CardTitle class="text-base">{{ selectedStatusLabel }}</CardTitle>
              <select
                v-model="selectedExperimentSummariesKey"
                class="border-input focus-visible:border-ring focus-visible:ring-ring/50 h-9 w-48 rounded-md border bg-transparent px-3 py-1 text-sm shadow-xs outline-none focus-visible:ring-3"
              >
                <option
                  v-for="opt in summaryOptions"
                  :key="opt.value"
                  :value="opt.value"
                >
                  {{ opt.text }} ({{ totalForKey(opt.value) }})
                </option>
              </select>
            </CardHeader>
            <CardContent>
              <Table v-if="items.length > 0">
                <TableHeader>
                  <TableRow>
                    <TableHead v-for="field in fields" :key="field.key">
                      {{ field.label }}
                    </TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  <TableRow v-for="item in items" :key="item.experiment_id">
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
              <p v-else class="py-6 text-center text-sm text-muted-foreground">
                No experiments in this range for the selected status.
              </p>
              <pager
                v-if="experimentStatistics.all_experiment_count > 0"
                :paginator="experimentStatisticsPaginator"
                @next="experimentStatisticsPaginator.next()"
                @previous="experimentStatisticsPaginator.previous()"
              ></pager>
            </CardContent>
          </Card>
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
  </main-layout>
</template>
<script>
import {
  BarChart3,
  CalendarDays,
  Filter as FilterIcon,
  Loader2,
  X,
} from "@lucide/vue";
import { errors, models, services, utils } from "django-airavata-api";
import { components, notifications } from "django-airavata-common-ui";
import {
  AreaChart,
  CurveType,
} from "django-airavata-common-ui/js/components/ui/chart-area";
import ExperimentDetailsView from "./ExperimentDetailsView";

import dayjs from "dayjs";

const MS_PER_HOUR = 60 * 60 * 1000;
const MS_PER_DAY = 24 * MS_PER_HOUR;
// Cap on concurrent per-bucket requests so long ranges stay responsive.
const MAX_BUCKETS = 30;

// The six status series plotted on the chart. `countKey`/`summaryKey` map to the
// ExperimentStatistics model's aggregate count + ExperimentSummary list fields.
// Colors use the shadcn design tokens (see app.css): neutral/primary for "all",
// then distinct accessible hues per status.
const SERIES_DEFS = [
  {
    key: "all",
    label: "All",
    countKey: "all_experiment_count",
    summaryKey: "all_experiments",
    color: "var(--primary)",
  },
  {
    key: "created",
    label: "Created",
    countKey: "created_experiment_count",
    summaryKey: "created_experiments",
    color: "var(--chart-3)",
  },
  {
    key: "running",
    label: "Running",
    countKey: "running_experiment_count",
    summaryKey: "running_experiments",
    color: "var(--warning)",
  },
  {
    key: "completed",
    label: "Completed",
    countKey: "completed_experiment_count",
    summaryKey: "completed_experiments",
    color: "var(--success)",
  },
  {
    key: "cancelled",
    label: "Cancelled",
    countKey: "cancelled_experiment_count",
    summaryKey: "cancelled_experiments",
    color: "var(--muted-foreground)",
  },
  {
    key: "failed",
    label: "Failed",
    countKey: "failed_experiment_count",
    summaryKey: "failed_experiments",
    color: "var(--destructive)",
  },
];

export default {
  name: "experiment-statistics-container",
  data() {
    // Default range: the last 24 hours, ending now.
    const toTime = new Date();
    const fromTime = new Date(toTime.getTime() - MS_PER_DAY);
    return {
      experimentStatisticsPaginator: null,
      selectedExperimentSummariesKey: "all_experiments",
      fromTime,
      toTime,
      dateRange: [fromTime, toTime],
      dateConfig: {
        mode: "range",
        dateFormat: "Y-m-d",
        maxDate: new Date(),
      },
      activeShortcut: "24h",
      suppressDateChange: false,
      loading: false,
      // Per-bucket aggregate counts: buckets[i] holds the ExperimentStatistics
      // results for the i-th time window.
      bucketStats: [],
      buckets: [],
      seriesVisible: SERIES_DEFS.reduce((acc, def) => {
        acc[def.key] = true;
        return acc;
      }, {}),
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
    FilterIcon,
    Loader2,
    X,
    ExperimentDetailsView,
    "area-chart": AreaChart,
    "application-name": components.ApplicationName,
    "compute-resource-name": components.ComputeResourceName,
    "human-date": components.HumanDate,
    "experiment-status-badge": components.ExperimentStatusBadge,
    "main-layout": components.MainLayout,
    pager: components.Pager,
  },
  computed: {
    rangeShortcuts() {
      return [
        { key: "24h", label: "Last 24 hours" },
        { key: "week", label: "Last week" },
        { key: "30d", label: "Last 30 days" },
      ];
    },
    anyFilterEnabled() {
      return (
        this.usernameFilterEnabled ||
        this.applicationNameFilterEnabled ||
        this.hostnameFilterEnabled
      );
    },
    allFiltersEnabled() {
      return (
        this.usernameFilterEnabled &&
        this.applicationNameFilterEnabled &&
        this.hostnameFilterEnabled
      );
    },
    // The aggregate ExperimentStatistics for the whole range (used by the
    // drill-down list + counts). Returned by the final/full-range request.
    experimentStatistics() {
      return this.experimentStatisticsPaginator
        ? this.experimentStatisticsPaginator.results
        : {};
    },
    // Chart series: each status' per-bucket count, in the series color, with the
    // current on/off visibility and a range total.
    series() {
      return SERIES_DEFS.map((def) => {
        const values = this.bucketStats.map(
          (stats) => (stats && stats[def.countKey]) || 0,
        );
        const total = values.reduce((sum, v) => sum + v, 0);
        return {
          key: def.key,
          label: def.label,
          color: def.color,
          visible: this.seriesVisible[def.key],
          values,
          total,
        };
      });
    },
    // Smooth (monotone) curve interpolation for the area/line series.
    curveType() {
      return CurveType.MonotoneX;
    },
    // The currently-visible series, used to build the chart categories/colors.
    visibleSeries() {
      return this.series.filter((s) => s.visible);
    },
    // Category keys (the series labels) for the AreaChart, in display order.
    visibleCategories() {
      return this.visibleSeries.map((s) => s.label);
    },
    // Remount the chart when the set of visible series changes so its internal
    // legend/crosshair state stays in sync with the categories/colors. Data-only
    // refreshes within the same set keep the same key (and animate in place).
    chartKey() {
      return this.visibleCategories.join("|");
    },
    // Colors aligned 1:1 with visibleCategories.
    visibleColors() {
      return this.visibleSeries.map((s) => s.color);
    },
    // One row per time bucket: { label: <x-axis tick>, <series label>: count }.
    // Only visible series are included so the chart redraws on toggle.
    chartData() {
      return this.buckets.map((bucket, i) => {
        const row = { label: bucket.label };
        for (const s of this.visibleSeries) {
          row[s.label] = s.values[i] ?? 0;
        }
        return row;
      });
    },
    rangeSummary() {
      const from = dayjs(this.fromTime).format("MMM D, YYYY HH:mm");
      const to = dayjs(this.toTime).format("MMM D, YYYY HH:mm");
      const n = this.buckets.length;
      const granularity = n > 0 ? this.buckets[0].granularity : "";
      return `${from} – ${to} · ${n} ${granularity} bucket${
        n === 1 ? "" : "s"
      }`;
    },
    fields() {
      return [
        { key: "name", label: "Name" },
        { key: "user_name", label: "Owner" },
        { key: "execution_id", label: "Application" },
        { key: "resource_host_id", label: "Resource" },
        { key: "creation_time", label: "Creation Time" },
        { key: "experiment_status", label: "Status" },
        { key: "actions", label: "Actions" },
      ];
    },
    summaryOptions() {
      return SERIES_DEFS.map((def) => ({
        value: def.summaryKey,
        text: `${def.label} Experiments`,
      }));
    },
    selectedStatusLabel() {
      const opt = this.summaryOptions.find(
        (o) => o.value === this.selectedExperimentSummariesKey,
      );
      return opt ? opt.text : "Experiments";
    },
    items() {
      return this.selectedExperimentSummaries;
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
        const options = this.appInterfaces.map((appInterface) => ({
          value: appInterface.application_interface_id,
          text: appInterface.application_name,
        }));
        return utils.StringUtils.sortIgnoreCase(options, (o) => o.text);
      } else {
        return [];
      }
    },
    hostnameOptions() {
      if (this.computeResourceNames && this.groupResourceProfiles) {
        // Only show compute resources that are configured in the Group Resource Profiles
        const groupResourceProfileCompResources = new Set(
          this.groupResourceProfiles.flatMap((grp) =>
            grp.compute_preferences.map((cp) => cp.compute_resource_id),
          ),
        );
        const options = this.computeResourceNames
          .filter((name) => groupResourceProfileCompResources.has(name.host_id))
          .map((name) => ({
            value: name.host_id,
            text: name.host,
          }));
        return utils.StringUtils.sortIgnoreCase(options, (o) => o.text);
      } else {
        return [];
      }
    },
  },
  methods: {
    // Compact count formatting for the Y axis (e.g. 1.2k, 3m).
    formatCount(value) {
      const n = Math.round(value);
      if (n >= 1e6) return (n / 1e6).toFixed(1).replace(/\.0$/, "") + "m";
      if (n >= 1e3) return (n / 1e3).toFixed(1).replace(/\.0$/, "") + "k";
      return String(n);
    },
    totalForKey(summaryKey) {
      const def = SERIES_DEFS.find((d) => d.summaryKey === summaryKey);
      const stats = this.experimentStatistics;
      return (def && stats && stats[def.countKey]) || 0;
    },
    toggleSeries(key) {
      this.seriesVisible = {
        ...this.seriesVisible,
        [key]: !this.seriesVisible[key],
      };
    },
    // Split [fromTime, toTime] into N time windows. Granularity adapts to the
    // range length to keep the bucket count at or below MAX_BUCKETS: hourly for
    // short ranges, daily for medium, weekly for long.
    computeBuckets() {
      const from = this.fromTime.getTime();
      const to = this.toTime.getTime();
      const span = Math.max(to - from, MS_PER_HOUR);

      let step;
      let granularity;
      if (span <= MAX_BUCKETS * MS_PER_HOUR) {
        step = MS_PER_HOUR;
        granularity = "hourly";
      } else if (span <= MAX_BUCKETS * MS_PER_DAY) {
        step = MS_PER_DAY;
        granularity = "daily";
      } else {
        step = 7 * MS_PER_DAY;
        granularity = "weekly";
      }
      // If even the chosen granularity exceeds the cap (very long custom ranges),
      // widen the step so the count stays within MAX_BUCKETS.
      let count = Math.ceil(span / step);
      if (count > MAX_BUCKETS) {
        step = Math.ceil(span / MAX_BUCKETS);
        count = MAX_BUCKETS;
        granularity = "interval";
      }

      const buckets = [];
      for (let i = 0; i < count; i++) {
        const start = from + i * step;
        const end = Math.min(start + step, to);
        if (start >= to) break;
        buckets.push({
          start,
          end,
          granularity,
          label:
            granularity === "hourly"
              ? dayjs(start).format("HH:mm")
              : dayjs(start).format("MMM D"),
        });
      }
      return buckets;
    },
    baseRequestParams() {
      const params = {};
      if (this.usernameFilterEnabled && this.usernameFilter) {
        params.userName = this.usernameFilter;
      }
      if (this.applicationNameFilterEnabled && this.applicationNameFilter) {
        params.applicationName = this.applicationNameFilter;
      }
      if (this.hostnameFilterEnabled && this.hostnameFilter) {
        params.resourceHostName = this.hostnameFilter;
      }
      return params;
    },
    async loadStatistics() {
      this.loading = true;
      const buckets = this.computeBuckets();
      const baseParams = this.baseRequestParams();
      try {
        // One aggregate request per bucket, issued concurrently, plus one
        // full-range request that feeds the drill-down list + total counts.
        const bucketPromises = buckets.map((bucket) =>
          services.ExperimentStatisticsService.get({
            ...baseParams,
            fromTime: new Date(bucket.start).toJSON(),
            toTime: new Date(bucket.end).toJSON(),
          }),
        );
        const fullRangePromise = services.ExperimentStatisticsService.get({
          ...baseParams,
          fromTime: this.fromTime.toJSON(),
          toTime: this.toTime.toJSON(),
        });
        const [fullRange, ...bucketResults] = await Promise.all([
          fullRangePromise,
          ...bucketPromises,
        ]);
        this.experimentStatisticsPaginator = fullRange;
        this.bucketStats = bucketResults.map((paginator) =>
          paginator ? paginator.results : null,
        );
        this.buckets = buckets;
      } catch (error) {
        utils.FetchUtils.reportError(error);
      } finally {
        this.loading = false;
      }
    },
    dateRangeChanged(selectedDates) {
      // Ignore the onChange that flatpickr fires when a shortcut updates the
      // picker programmatically; that path already set the range + reloaded.
      if (this.suppressDateChange) {
        return;
      }
      if (selectedDates.length === 2) {
        this.fromTime = selectedDates[0];
        // flatpickr range end is midnight of the end day; include the whole day.
        this.toTime = new Date(selectedDates[1].getTime() + MS_PER_DAY);
        this.activeShortcut = null;
        this.loadStatistics();
      }
    },
    applyShortcut(key) {
      const to = new Date();
      let from;
      if (key === "24h") {
        from = new Date(to.getTime() - MS_PER_DAY);
      } else if (key === "week") {
        from = new Date(to.getTime() - 7 * MS_PER_DAY);
      } else {
        from = new Date(to.getTime() - 30 * MS_PER_DAY);
      }
      this.fromTime = from;
      this.toTime = to;
      this.activeShortcut = key;
      // Update the picker without letting its onChange clobber the shortcut
      // state; reset the flag after the change has been flushed.
      this.suppressDateChange = true;
      this.dateRange = [from, to];
      this.$nextTick(() => {
        this.suppressDateChange = false;
      });
      this.loadStatistics();
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
  },
};
</script>
