<template>
  <div>
    <BreadcrumbNav :crumbs="breadcrumbs" />
    <div class="row align-items-center mb-3">
      <div class="col">
        <h1 class="h4 mb-0">Experiments</h1>
        <p class="text-muted mb-0">Search, view, and manage your computational experiments.</p>
      </div>
      <div class="col-auto">
        <a href="/workspace/launch" class="btn btn-primary btn-sm"
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
                    <a href="/workspace/launch">Dashboard</a>.
                  </div>
                </div>
              </td>
            </tr>
            <tr v-for="experiment in experiments || []" :key="(experiment as any).experiment_id">
              <td>
                <a :href="viewLink(experiment)">{{ (experiment as any).name }}</a>
              </td>
              <td v-if="applicationName(experiment)">{{ applicationName(experiment) }}</td>
              <td v-else class="text-muted">N/A</td>
              <td>{{ (experiment as any).user_name }}</td>
              <td>
                <span :title="(experiment as any).creation_time">{{
                  fromNow((experiment as any).creation_time)
                }}</span>
              </td>
              <td><ExperimentStatusBadge :status-name="(experiment as any).experiment_status.name" /></td>
              <td class="text-nowrap" style="width: 1%">
                <div
                  v-if="applicationName(experiment)"
                  class="d-flex gap-2 justify-content-end flex-nowrap"
                >
                  <a
                    v-if="(experiment as any).isEditable"
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
        <Pager
          v-if="experiments && experiments.length > 0 && experimentsPaginator"
          :paginator="experimentsPaginator"
          @next="nextExperiments"
          @previous="previousExperiments"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onBeforeMount, reactive } from "vue";
import { errors, services, utils } from "django-airavata-api";
import { components as comps } from "django-airavata-common-ui";
import flatPickr from "vue-flatpickr-component";
import "flatpickr/dist/flatpickr.css";

import { relativeTime } from "django-airavata-common-ui/js/utils/dates.js";
import urls from "../utils/urls";

const BreadcrumbNav = comps.BreadcrumbNav;
const Pager = comps.Pager;
const ExperimentStatusBadge = comps.ExperimentStatusBadge;

const props = withDefaults(defineProps<{
  initialExperimentsData?: unknown | null;
  projectId?: string | null;
  breadcrumbs?: unknown[];
}>(), {
  initialExperimentsData: undefined,
  projectId: null,
  breadcrumbs: () => [],
});

const experimentsPaginator = ref<unknown>(null);
const applicationInterfaces = reactive<Record<string, unknown>>({});
const search = ref<string | null>(null);
const applicationSelect = ref<string | null>(null);
const dateSelect = ref<string | null>(null);
const experimentAttributeSelect = ref<string | null>(null);
const experimentStatusSelect = ref<string | null>(null);
const appInterfaces = ref<unknown[] | null>(null);
const fromDate = ref<Date | null>(null);
const toDate = ref<Date | null>(null);
const applicationSelected = ref(false);
const defaultOptionSelected = ref(true);
const dateConfig = {
  mode: "range" as const,
  wrap: true,
  dateFormat: "Y-m-d",
  maxDate: new Date(Date.now() + 86400000),
};

const experiments = computed<unknown[] | null>(() =>
  experimentsPaginator.value ? (experimentsPaginator.value as { results: unknown[] }).results : null,
);

const applicationNameOptions = computed(() => {
  if (appInterfaces.value) {
    const options = (appInterfaces.value as Array<{ application_interface_id: string; application_name: string }>).map((appIface) => ({
      value: appIface.application_interface_id,
      text: appIface.application_name,
    }));
    return utils.StringUtils.sortIgnoreCase(options, (o: { text: string }) => o.text);
  } else {
    return [];
  }
});

function searchExperiments() {
  experimentsPaginator.value = null;
  reloadExperiments();
}

function resetSearch() {
  experimentsPaginator.value = null;
  search.value = null;
  experimentAttributeSelect.value = null;
  experimentStatusSelect.value = null;
  applicationSelect.value = null;
  dateSelect.value = null;
  toDate.value = null;
  fromDate.value = null;
  checkSearchOptions();
  reloadExperiments();
}

function reloadExperiments() {
  const searchParams: Record<string, unknown> = {};
  if (props.projectId) {
    searchParams["PROJECT_ID"] = props.projectId;
  }
  if (experimentAttributeSelect.value) {
    if (experimentAttributeSelect.value === "APPLICATION_ID" && applicationSelect.value) {
      searchParams["APPLICATION_ID"] = applicationSelect.value;
    } else if (search.value) {
      searchParams[experimentAttributeSelect.value] = search.value;
    }
  }
  if (experimentStatusSelect.value) {
    if (experimentStatusSelect.value !== "ALL") {
      searchParams["STATUS"] = experimentStatusSelect.value;
    }
  }
  if (fromDate.value && toDate.value) {
    searchParams["FROM_DATE"] = fromDate.value.getTime();
    searchParams["TO_DATE"] = toDate.value.getTime();
  }

  services.ExperimentSearchService.list(searchParams).then(
    (result: unknown) => (experimentsPaginator.value = result),
  );
}

function checkSearchOptions() {
  applicationSelected.value = false;
  defaultOptionSelected.value = false;
  if (experimentAttributeSelect.value === "APPLICATION_ID") {
    applicationSelected.value = true;
  } else {
    defaultOptionSelected.value = true;
  }
}

function loadApplicationInterfaces() {
  return services.ApplicationInterfaceService.list().then(
    (ifaces: unknown) => (appInterfaces.value = ifaces as unknown[]),
  );
}

function dateRangeChanged(selectedDates: Date[]) {
  [fromDate.value, toDate.value] = selectedDates;
  if (fromDate.value && toDate.value) {
    reloadExperiments();
  }
}

function nextExperiments() {
  (experimentsPaginator.value as { next(): void }).next();
}

function previousExperiments() {
  (experimentsPaginator.value as { previous(): void }).previous();
}

function fromNow(date: unknown): string {
  return relativeTime(date as string | number | Date);
}

function editLink(experiment: unknown): string {
  return urls.editExperiment(props.projectId ?? "", experiment as { experiment_id: string });
}

function viewLink(experiment: unknown): string {
  return urls.viewExperiment(props.projectId ?? "", experiment as { experiment_id: string });
}

function applicationName(experiment: unknown): string | null {
  const exp = experiment as { execution_id: string; experiment_id: string };
  if (exp.execution_id in applicationInterfaces) {
    const iface = applicationInterfaces[exp.execution_id];
    if (iface instanceof Object && "application_name" in iface) {
      return (iface as { application_name: string }).application_name;
    } else if (iface === null) {
      return null;
    }
  } else {
    const request = services.ApplicationInterfaceService.retrieve(
      { lookup: exp.execution_id },
      { ignoreErrors: true },
    )
      .then((result: unknown) => {
        applicationInterfaces[exp.execution_id] = result;
      })
      .catch((error: unknown) => {
        if (errors.ErrorUtils.isNotFoundError(error)) {
          applicationInterfaces[exp.execution_id] = null;
        } else {
          throw error;
        }
      })
      .catch(utils.FetchUtils.reportError);
    applicationInterfaces[exp.execution_id] = request;
  }
  return "...";
}

function clone(experiment: unknown) {
  const exp = experiment as { experiment_id: string };
  services.ExperimentService.clone({
    lookup: exp.experiment_id,
  }).then((clonedExperiment: unknown) => {
    urls.navigateToEditExperiment(props.projectId ?? "", clonedExperiment as { experiment_id: string });
  });
}

onBeforeMount(() => {
  loadApplicationInterfaces();
  services.ExperimentSearchService.list({
    initialData: props.initialExperimentsData,
  }).then((result: unknown) => (experimentsPaginator.value = result));
});
</script>

<style></style>
