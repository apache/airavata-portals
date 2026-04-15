<template>
  <div>
    <div class="row align-items-center mb-3">
      <div class="col">
        <h1 class="h4 mb-0">Home</h1>
        <p class="text-muted mb-0">
          Overview of your experiments and recent activity.
        </p>
      </div>
    </div>

    <!-- Experiments overview chart -->
    <div class="card mb-4">
      <div class="card-header d-flex align-items-center">
        <h5 class="mb-0">Experiments Overview</h5>
        <small class="text-muted ms-2">({{ filteredTotal }} experiments)</small>
        <div
          class="btn-group btn-group-sm ms-auto"
          role="group"
        >
          <button
            v-for="r in ranges"
            :key="r.key"
            :class="['btn', range === r.key ? 'btn-primary' : 'btn-outline-primary']"
            @click="range = r.key"
          >{{ r.label }}</button>
        </div>
      </div>
      <div
        class="card-body"
        style="height: 280px;"
      >
        <div
          v-if="loading"
          class="text-center text-muted py-5"
        >
          <i class="fa fa-spinner fa-spin me-1"></i>Loading...
        </div>
        <Bar
          v-else
          :data="chartData"
          :options="chartOptions"
        />
      </div>
    </div>

    <!-- Recent experiments table -->
    <div class="card mb-4">
      <div class="card-header d-flex align-items-center">
        <h5 class="mb-0">Recent Experiments</h5>
        <div class="ms-auto d-flex gap-2">
          <a
            href="/workspace/applications"
            class="btn btn-primary btn-sm"
          >
            <i class="fa fa-plus me-1"></i>New Experiment
          </a>
          <a
            href="/workspace/projects"
            class="btn btn-outline-secondary btn-sm"
          >
            <i class="fa fa-folder-plus me-1"></i>New Project
          </a>
        </div>
      </div>
      <div class="card-body p-0">
        <div v-if="loading" class="p-4 text-center text-muted">
          <i class="fa fa-spinner fa-spin me-1"></i>Loading experiments...
        </div>
        <div
          v-else-if="pagedExperiments.length === 0"
          class="p-4 text-center text-muted fst-italic"
        >
          No experiments yet. Click "New Experiment" to get started.
        </div>
        <table v-else class="table table-hover table-sm mb-0">
          <thead>
            <tr>
              <th>Name</th>
              <th>Project</th>
              <th>Application</th>
              <th>Status</th>
              <th>Created</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="exp in pagedExperiments"
              :key="exp.experiment_id"
            >
              <td>
                <a
                  :href="viewExperimentUrl(exp)"
                  class="text-decoration-none fw-semibold"
                >{{ exp.name }}</a>
              </td>
              <td>{{ projectName(exp.project_id) }}</td>
              <td>{{ applicationName(exp.execution_id) }}</td>
              <td>
                <span
                  class="badge"
                  :class="statusBadgeClass(exp.experiment_status && exp.experiment_status.name)"
                >{{ exp.experiment_status && exp.experiment_status.name }}</span>
              </td>
              <td>
                <span
                  v-if="exp.creation_time"
                  :title="exp.creation_time.toLocaleString()"
                >{{ formatDate(exp.creation_time) }}</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <div
        v-if="!loading && totalPages > 1"
        class="card-footer d-flex align-items-center justify-content-between"
      >
        <small class="text-muted">
          Page {{ currentPage }} of {{ totalPages }} ({{ recentExperiments.length }} experiments)
        </small>
        <div class="btn-group btn-group-sm">
          <button
            class="btn btn-outline-secondary"
            :disabled="currentPage <= 1"
            @click="currentPage--"
          >
            <i class="fa fa-chevron-left"></i>
          </button>
          <button
            class="btn btn-outline-secondary"
            :disabled="currentPage >= totalPages"
            @click="currentPage++"
          >
            <i class="fa fa-chevron-right"></i>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { services } from "django-airavata-api";
import { Bar } from "vue-chartjs";
import {
  Chart,
  Title,
  Tooltip,
  Legend,
  BarElement,
  CategoryScale,
  LinearScale,
} from "chart.js";

Chart.register(Title, Tooltip, Legend, BarElement, CategoryScale, LinearScale);

const RUNNING_STATES = ["EXECUTING", "SCHEDULED", "LAUNCHED", "VALIDATED"];
const COMPLETED_STATES = ["COMPLETED"];
const FAILED_STATES = ["FAILED", "CANCELED", "CANCELING"];

function classifyState(name) {
  if (RUNNING_STATES.includes(name)) {
    return "running";
  }
  if (COMPLETED_STATES.includes(name)) {
    return "completed";
  }
  if (FAILED_STATES.includes(name)) {
    return "failed";
  }
  return "other";
}

function startOfMonth(d) {
  return new Date(d.getFullYear(), d.getMonth(), 1);
}

function addMonths(d, n) {
  return new Date(d.getFullYear(), d.getMonth() + n, 1);
}

function bucketsFor(range, now, experiments) {
  if (range === "1d") {
    const starts = [];
    const anchor = new Date(now);
    anchor.setMinutes(0, 0, 0);
    anchor.setHours(anchor.getHours() - 23);
    for (let i = 0; i < 24; i++) {
      starts.push(new Date(anchor.getTime() + i * 3600e3));
    }
    return {
      starts,
      sizes: starts.map(() => 3600e3),
      format: (d) => String(d.getHours()).padStart(2, "0") + ":00",
    };
  }
  if (range === "7d") {
    const starts = [];
    const anchor = new Date(now);
    anchor.setHours(0, 0, 0, 0);
    anchor.setDate(anchor.getDate() - 6);
    for (let i = 0; i < 7; i++) {
      starts.push(new Date(anchor.getTime() + i * 86400e3));
    }
    return {
      starts,
      sizes: starts.map(() => 86400e3),
      format: (d) =>
        d.toLocaleDateString(undefined, {
          weekday: "short",
          month: "short",
          day: "numeric",
        }),
    };
  }
  if (range === "1mo") {
    const starts = [];
    const anchor = new Date(now);
    anchor.setHours(0, 0, 0, 0);
    anchor.setDate(anchor.getDate() - 29);
    for (let i = 0; i < 30; i++) {
      starts.push(new Date(anchor.getTime() + i * 86400e3));
    }
    return {
      starts,
      sizes: starts.map(() => 86400e3),
      format: (d) =>
        d.toLocaleDateString(undefined, { month: "short", day: "numeric" }),
    };
  }
  if (range === "1y") {
    const starts = [];
    const anchorMonth = startOfMonth(now);
    const first = addMonths(anchorMonth, -11);
    for (let i = 0; i < 12; i++) {
      starts.push(addMonths(first, i));
    }
    const sizes = starts.map((s, i) => {
      const next = i < 11 ? starts[i + 1] : addMonths(s, 1);
      return next.getTime() - s.getTime();
    });
    return {
      starts,
      sizes,
      format: (d) =>
        d.toLocaleDateString(undefined, { month: "short", year: "numeric" }),
    };
  }
  // 'all'
  let earliest = null;
  experiments.forEach((e) => {
    if (e.creation_time && (!earliest || e.creation_time < earliest)) {
      earliest = e.creation_time;
    }
  });
  if (!earliest) {
    earliest = now;
  }
  const starts = [];
  let cursor = startOfMonth(earliest);
  const end = startOfMonth(now);
  // safety cap
  let guard = 0;
  while (cursor.getTime() <= end.getTime() && guard < 600) {
    starts.push(new Date(cursor));
    cursor = addMonths(cursor, 1);
    guard++;
  }
  if (starts.length === 0) {
    starts.push(startOfMonth(now));
  }
  const sizes = starts.map((s, i) => {
    const next = i < starts.length - 1 ? starts[i + 1] : addMonths(s, 1);
    return next.getTime() - s.getTime();
  });
  return {
    starts,
    sizes,
    format: (d) =>
      d.toLocaleDateString(undefined, { month: "short", year: "numeric" }),
  };
}

export default {
  name: "workspace-dashboard-container",
  components: { Bar },
  data() {
    return {
      experiments: [],
      projectsById: {},
      applicationInterfaces: {},
      loading: true,
      currentPage: 1,
      pageSize: 10,
      range: "7d",
      ranges: [
        { key: "1d", label: "1 day" },
        { key: "7d", label: "7 days" },
        { key: "1mo", label: "1 month" },
        { key: "1y", label: "1 year" },
        { key: "all", label: "All" },
      ],
    };
  },
  computed: {
    runningCount() {
      return this.experiments.filter((e) =>
        RUNNING_STATES.includes(this.statusName(e))
      ).length;
    },
    completedCount() {
      return this.experiments.filter((e) =>
        COMPLETED_STATES.includes(this.statusName(e))
      ).length;
    },
    failedCount() {
      return this.experiments.filter((e) =>
        FAILED_STATES.includes(this.statusName(e))
      ).length;
    },
    totalCount() {
      return this.experiments.length;
    },
    recentExperiments() {
      // Sort by creation_time desc
      return [...this.experiments].sort((a, b) => {
        const ta = a.creation_time ? a.creation_time.getTime() : 0;
        const tb = b.creation_time ? b.creation_time.getTime() : 0;
        return tb - ta;
      });
    },
    totalPages() {
      return Math.max(
        1,
        Math.ceil(this.recentExperiments.length / this.pageSize)
      );
    },
    pagedExperiments() {
      const start = (this.currentPage - 1) * this.pageSize;
      return this.recentExperiments.slice(start, start + this.pageSize);
    },
    otherCount() {
      return Math.max(
        0,
        this.totalCount -
          this.runningCount -
          this.completedCount -
          this.failedCount
      );
    },
    bucketSpec() {
      return bucketsFor(this.range, new Date(), this.experiments);
    },
    filteredExperiments() {
      const spec = this.bucketSpec;
      if (!spec.starts.length) {
        return [];
      }
      const min = spec.starts[0].getTime();
      const lastIdx = spec.starts.length - 1;
      const max = spec.starts[lastIdx].getTime() + spec.sizes[lastIdx];
      return this.experiments.filter((e) => {
        if (!e.creation_time) {
          return false;
        }
        const t = e.creation_time.getTime();
        return t >= min && t < max;
      });
    },
    filteredTotal() {
      return this.filteredExperiments.length;
    },
    chartData() {
      const spec = this.bucketSpec;
      const n = spec.starts.length;
      const running = new Array(n).fill(0);
      const completed = new Array(n).fill(0);
      const failed = new Array(n).fill(0);
      const other = new Array(n).fill(0);

      const bucketIndex = (t) => {
        // linear search since bucket sizes may vary (months)
        for (let i = 0; i < n; i++) {
          const start = spec.starts[i].getTime();
          const end = start + spec.sizes[i];
          if (t >= start && t < end) {
            return i;
          }
        }
        return -1;
      };

      this.filteredExperiments.forEach((e) => {
        const idx = bucketIndex(e.creation_time.getTime());
        if (idx < 0) {
          return;
        }
        const cls = classifyState(this.statusName(e));
        if (cls === "running") {
          running[idx]++;
        } else if (cls === "completed") {
          completed[idx]++;
        } else if (cls === "failed") {
          failed[idx]++;
        } else {
          other[idx]++;
        }
      });

      return {
        labels: spec.starts.map((d) => spec.format(d)),
        datasets: [
          {
            label: "Running",
            data: running,
            backgroundColor: "#0d6efd",
            stack: "exp",
          },
          {
            label: "Completed",
            data: completed,
            backgroundColor: "#198754",
            stack: "exp",
          },
          {
            label: "Failed",
            data: failed,
            backgroundColor: "#dc3545",
            stack: "exp",
          },
          {
            label: "Other",
            data: other,
            backgroundColor: "#6c757d",
            stack: "exp",
          },
        ],
      };
    },
    chartOptions() {
      return {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: true, position: "bottom" },
          tooltip: {
            callbacks: {
              label: (ctx) =>
                ` ${ctx.dataset.label}: ${ctx.parsed.y} experiment(s)`,
            },
          },
        },
        scales: {
          x: { stacked: true },
          y: {
            stacked: true,
            beginAtZero: true,
            ticks: { precision: 0 },
          },
        },
      };
    },
  },
  mounted() {
    this.loadDashboard();
  },
  methods: {
    statusName(exp) {
      return exp.experiment_status && exp.experiment_status.name;
    },
    statusBadgeClass(stateName) {
      if (!stateName) {
        return "bg-secondary";
      }
      if (RUNNING_STATES.includes(stateName)) {
        return "bg-primary";
      }
      if (COMPLETED_STATES.includes(stateName)) {
        return "bg-success";
      }
      if (FAILED_STATES.includes(stateName)) {
        return "bg-danger";
      }
      // CREATED and anything else
      return "bg-secondary";
    },
    formatDate(d) {
      if (!d) {
        return "";
      }
      try {
        return d.toLocaleDateString(undefined, {
          year: "numeric",
          month: "short",
          day: "numeric",
        });
      } catch (e) {
        return String(d);
      }
    },
    projectName(projectId) {
      if (!projectId) {
        return "";
      }
      const p = this.projectsById[projectId];
      return p ? p.name : projectId;
    },
    applicationName(interfaceId) {
      if (!interfaceId) {
        return "";
      }
      const ai = this.applicationInterfaces[interfaceId];
      if (ai && ai.application_name) {
        return ai.application_name;
      }
      return "";
    },
    viewExperimentUrl(exp) {
      return (
        "/workspace/projects/" +
        encodeURIComponent(exp.project_id) +
        "/experiments/" +
        encodeURIComponent(exp.experiment_id) +
        "/"
      );
    },
    loadDashboard() {
      this.loading = true;
      const expPromise = services.ExperimentSearchService.list(
        {
          limit: 100,
          offset: 0,
        },
        {
          showSpinner: false,
          ignoreErrors: true,
        }
      )
        .then((result) => {
          this.experiments =
            result && Array.isArray(result.results) ? result.results : [];
        })
        .catch(() => {
          this.experiments = [];
        });

      const projPromise = services.ProjectService.list()
        .then((result) => {
          let list = [];
          if (Array.isArray(result)) {
            list = result;
          } else if (result && Array.isArray(result.results)) {
            list = result.results;
          }
          const map = {};
          list.forEach((p) => {
            const id = p.projectId || p.project_id;
            if (id) {
              map[id] = p;
            }
          });
          this.projectsById = map;
        })
        .catch(() => {
          this.projectsById = {};
        });

      Promise.all([expPromise, projPromise]).then(() => {
        this.loading = false;
        this.loadApplicationInterfaces();
      });
    },
    loadApplicationInterfaces() {
      const ids = {};
      this.experiments.forEach((e) => {
        if (e.execution_id) {
          ids[e.execution_id] = true;
        }
      });
      Object.keys(ids).forEach((interfaceId) => {
        if (interfaceId in this.applicationInterfaces) {
          return;
        }
        services.ApplicationInterfaceService.retrieve(
          { lookup: interfaceId },
          { showSpinner: false, ignoreErrors: true }
        )
          .then((ai) => {
            this.$set(this.applicationInterfaces, interfaceId, ai);
          })
          .catch(() => {
            this.$set(this.applicationInterfaces, interfaceId, null);
          });
      });
    },
  },
};
</script>
