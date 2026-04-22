<template>
  <div>
    <div class="row align-items-center mb-3">
      <div class="col">
        <h1 class="h4 mb-0">Home</h1>
        <p class="text-muted mb-0">Overview of your experiments and recent activity.</p>
      </div>
    </div>

    <!-- Experiments overview chart -->
    <div class="card mb-4">
      <div class="card-header d-flex align-items-center">
        <h5 class="mb-0">Experiments Overview</h5>
        <small class="text-muted ms-2">({{ filteredTotal }} experiments)</small>
        <div class="btn-group btn-group-sm ms-auto" role="group">
          <button
            v-for="r in ranges"
            :key="r.key"
            :class="['btn', range === r.key ? 'btn-primary' : 'btn-outline-primary']"
            @click="range = r.key"
          >
            {{ r.label }}
          </button>
        </div>
      </div>
      <div class="card-body" style="height: 280px">
        <div v-if="loading" class="text-center text-muted py-5">
          <i class="fa fa-spinner fa-spin me-1"></i>Loading...
        </div>
        <Bar v-else :data="chartData" :options="chartOptions" />
      </div>
    </div>

    <!-- Recent experiments table -->
    <div class="card mb-4">
      <div class="card-header d-flex align-items-center">
        <h5 class="mb-0">Recent Experiments</h5>
        <div class="ms-auto d-flex gap-2">
          <a
            href="/workspace/applications?action=launch"
            class="btn btn-primary btn-sm"
            title="Choose an application to run an experiment from"
          >
            <i class="fa fa-rocket me-1"></i>Launch Experiment
          </a>
          <a href="/workspace/projects" class="btn btn-outline-secondary btn-sm">
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
          No experiments yet. Click "Launch Experiment" to get started.
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
            <tr v-for="exp in pagedExperiments" :key="(exp as Record<string, unknown>).experiment_id as string">
              <td>
                <a :href="viewExperimentUrl(exp as Record<string, unknown>)" class="text-decoration-none fw-semibold">{{
                  (exp as Record<string, unknown>).name
                }}</a>
              </td>
              <td>{{ projectName((exp as Record<string, unknown>).project_id as string) }}</td>
              <td>{{ applicationName((exp as Record<string, unknown>).execution_id as string) }}</td>
              <td>
                <span
                  class="badge"
                  :class="statusBadgeClass(((exp as Record<string, unknown>).experiment_status as Record<string, unknown> | undefined)?.name as string | undefined)"
                  >{{ (exp as Record<string, unknown>).experiment_status && ((exp as Record<string, unknown>).experiment_status as Record<string, unknown>).name }}</span
                >
              </td>
              <td>
                <span v-if="(exp as Record<string, unknown>).creation_time" :title="((exp as Record<string, unknown>).creation_time as Date).toLocaleString()">{{
                  formatDate((exp as Record<string, unknown>).creation_time as Date)
                }}</span>
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

<script setup lang="ts">
import { ref, computed, onMounted, reactive } from "vue";
import { services } from "django-airavata-api";
import { Bar } from "vue-chartjs";
import { Chart, Title, Tooltip, Legend, BarElement, CategoryScale, LinearScale } from "chart.js";

Chart.register(Title, Tooltip, Legend, BarElement, CategoryScale, LinearScale);

const RUNNING_STATES = ["EXECUTING", "SCHEDULED", "LAUNCHED", "VALIDATED"];
const COMPLETED_STATES = ["COMPLETED"];
const FAILED_STATES = ["FAILED", "CANCELED", "CANCELING"];

function classifyState(name: string | undefined): string {
  if (!name) return "other";
  if (RUNNING_STATES.includes(name)) return "running";
  if (COMPLETED_STATES.includes(name)) return "completed";
  if (FAILED_STATES.includes(name)) return "failed";
  return "other";
}

function startOfMonth(d: Date): Date {
  return new Date(d.getFullYear(), d.getMonth(), 1);
}

function addMonths(d: Date, n: number): Date {
  return new Date(d.getFullYear(), d.getMonth() + n, 1);
}

interface BucketSpec {
  starts: Date[];
  sizes: number[];
  format: (_d: Date) => string;
}

function bucketsFor(rangeKey: string, now: Date, experiments: unknown[]): BucketSpec {
  if (rangeKey === "1d") {
    const starts: Date[] = [];
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
  if (rangeKey === "7d") {
    const starts: Date[] = [];
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
  if (rangeKey === "1mo") {
    const starts: Date[] = [];
    const anchor = new Date(now);
    anchor.setHours(0, 0, 0, 0);
    anchor.setDate(anchor.getDate() - 29);
    for (let i = 0; i < 30; i++) {
      starts.push(new Date(anchor.getTime() + i * 86400e3));
    }
    return {
      starts,
      sizes: starts.map(() => 86400e3),
      format: (d) => d.toLocaleDateString(undefined, { month: "short", day: "numeric" }),
    };
  }
  if (rangeKey === "1y") {
    const starts: Date[] = [];
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
      format: (d) => d.toLocaleDateString(undefined, { month: "short", year: "numeric" }),
    };
  }
  // 'all'
  let earliest: Date | null = null;
  (experiments as Array<Record<string, unknown>>).forEach((e) => {
    if (e.creation_time && (!earliest || (e.creation_time as Date) < earliest)) {
      earliest = e.creation_time as Date;
    }
  });
  if (!earliest) {
    earliest = now;
  }
  const starts: Date[] = [];
  let cursor = startOfMonth(earliest);
  const end = startOfMonth(now);
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
    format: (d) => d.toLocaleDateString(undefined, { month: "short", year: "numeric" }),
  };
}

const experiments = ref<unknown[]>([]);
const projectsById = reactive<Record<string, unknown>>({});
const applicationInterfaces = reactive<Record<string, unknown>>({});
const loading = ref(true);
const currentPage = ref(1);
const pageSize = 10;
const range = ref("7d");
const ranges = [
  { key: "1d", label: "1 day" },
  { key: "7d", label: "7 days" },
  { key: "1mo", label: "1 month" },
  { key: "1y", label: "1 year" },
  { key: "all", label: "All" },
];

function statusName(exp: Record<string, unknown>): string | undefined {
  const status = exp.experiment_status as Record<string, unknown> | undefined;
  return status ? (status.name as string) : undefined;
}

const recentExperiments = computed<unknown[]>(() => {
  return [...experiments.value].sort((a, b) => {
    const ea = a as Record<string, unknown>;
    const eb = b as Record<string, unknown>;
    const ta = ea.creation_time ? (ea.creation_time as Date).getTime() : 0;
    const tb = eb.creation_time ? (eb.creation_time as Date).getTime() : 0;
    return tb - ta;
  });
});

const totalPages = computed(() =>
  Math.max(1, Math.ceil(recentExperiments.value.length / pageSize)),
);

const pagedExperiments = computed(() => {
  const start = (currentPage.value - 1) * pageSize;
  return recentExperiments.value.slice(start, start + pageSize);
});

const bucketSpec = computed(() => bucketsFor(range.value, new Date(), experiments.value));

const filteredExperiments = computed<unknown[]>(() => {
  const spec = bucketSpec.value;
  if (!spec.starts.length) return [];
  const min = spec.starts[0].getTime();
  const lastIdx = spec.starts.length - 1;
  const max = spec.starts[lastIdx].getTime() + spec.sizes[lastIdx];
  return experiments.value.filter((e) => {
    const exp = e as Record<string, unknown>;
    if (!exp.creation_time) return false;
    const t = (exp.creation_time as Date).getTime();
    return t >= min && t < max;
  });
});

const filteredTotal = computed(() => filteredExperiments.value.length);

const chartData = computed(() => {
  const spec = bucketSpec.value;
  const n = spec.starts.length;
  const running = new Array<number>(n).fill(0);
  const completed = new Array<number>(n).fill(0);
  const failed = new Array<number>(n).fill(0);
  const other = new Array<number>(n).fill(0);

  const bucketIndex = (t: number): number => {
    for (let i = 0; i < n; i++) {
      const start = spec.starts[i].getTime();
      const end = start + spec.sizes[i];
      if (t >= start && t < end) return i;
    }
    return -1;
  };

  filteredExperiments.value.forEach((e) => {
    const exp = e as Record<string, unknown>;
    const idx = bucketIndex((exp.creation_time as Date).getTime());
    if (idx < 0) return;
    const cls = classifyState(statusName(exp));
    if (cls === "running") running[idx]++;
    else if (cls === "completed") completed[idx]++;
    else if (cls === "failed") failed[idx]++;
    else other[idx]++;
  });

  return {
    labels: spec.starts.map((d) => spec.format(d)),
    datasets: [
      { label: "Running", data: running, backgroundColor: "#0d6efd", stack: "exp" },
      { label: "Completed", data: completed, backgroundColor: "#198754", stack: "exp" },
      { label: "Failed", data: failed, backgroundColor: "#dc3545", stack: "exp" },
      { label: "Other", data: other, backgroundColor: "#6c757d", stack: "exp" },
    ],
  };
});

const chartOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: true, position: "bottom" as const },
    tooltip: {
      callbacks: {
        label: (ctx: unknown) => {
          const c = ctx as { dataset?: { label?: string }; parsed?: { y?: number } };
          return ` ${c.dataset?.label ?? ""}: ${c.parsed?.y ?? 0} experiment(s)`;
        },
      },
    },
  },
  scales: {
    x: { stacked: true },
    y: { stacked: true, beginAtZero: true, ticks: { precision: 0 } },
  },
}));

function statusBadgeClass(stateName: string | undefined): string {
  if (!stateName) return "bg-secondary";
  if (RUNNING_STATES.includes(stateName)) return "bg-primary";
  if (COMPLETED_STATES.includes(stateName)) return "bg-success";
  if (FAILED_STATES.includes(stateName)) return "bg-danger";
  return "bg-secondary";
}

function formatDate(d: Date | null | undefined): string {
  if (!d) return "";
  try {
    return d.toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
  } catch (e) {
    return String(d);
  }
}

function projectName(projectId: string | undefined): string {
  if (!projectId) return "";
  const p = projectsById[projectId] as Record<string, unknown> | undefined;
  return p ? (p.name as string) : projectId;
}

function applicationName(interfaceId: string | undefined): string {
  if (!interfaceId) return "";
  const ai = applicationInterfaces[interfaceId] as Record<string, unknown> | undefined;
  if (ai && ai.application_name) return ai.application_name as string;
  return "";
}

function viewExperimentUrl(exp: Record<string, unknown>): string {
  return (
    "/workspace/projects/" +
    encodeURIComponent(exp.project_id as string) +
    "/experiments/" +
    encodeURIComponent(exp.experiment_id as string) +
    "/"
  );
}

function loadDashboard(): void {
  loading.value = true;
  const expPromise = services.ExperimentSearchService.list(
    { limit: 100, offset: 0 },
    { showSpinner: false, ignoreErrors: true },
  )
    .then((result: unknown) => {
      const r = result as { results?: unknown[] } | null;
      experiments.value = r && Array.isArray(r.results) ? r.results : [];
    })
    .catch(() => {
      experiments.value = [];
    });

  const projPromise = services.ProjectService.list()
    .then((result: unknown) => {
      let list: Array<Record<string, unknown>> = [];
      if (Array.isArray(result)) {
        list = result as Array<Record<string, unknown>>;
      } else {
        const r = result as { results?: Array<Record<string, unknown>> } | null;
        if (r && Array.isArray(r.results)) {
          list = r.results;
        }
      }
      list.forEach((p) => {
        const id = (p.projectId || p.project_id) as string | undefined;
        if (id) {
          projectsById[id] = p;
        }
      });
    })
    .catch(() => {
      // projectsById stays as-is
    });

  Promise.all([expPromise, projPromise]).then(() => {
    loading.value = false;
    loadApplicationInterfaces();
  });
}

function loadApplicationInterfaces(): void {
  const ids: Record<string, boolean> = {};
  (experiments.value as Array<Record<string, unknown>>).forEach((e) => {
    if (e.execution_id) {
      ids[e.execution_id as string] = true;
    }
  });
  Object.keys(ids).forEach((interfaceId) => {
    if (interfaceId in applicationInterfaces) return;
    services.ApplicationInterfaceService.retrieve(
      { lookup: interfaceId },
      { showSpinner: false, ignoreErrors: true },
    )
      .then((ai: unknown) => {
        applicationInterfaces[interfaceId] = ai;
      })
      .catch(() => {
        applicationInterfaces[interfaceId] = null;
      });
  });
}

onMounted(() => {
  loadDashboard();
});
</script>
