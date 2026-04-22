<template>
  <div>
    <PgaLink />
    <div class="row align-items-center mb-3">
      <div class="col">
        <h1 class="h4 mb-0">Applications</h1>
        <p class="text-muted mb-0">Manage applications and launch experiments.</p>
      </div>
      <div class="col-auto">
        <a href="/workspace/applications/new" class="btn btn-primary btn-sm">
          <i class="fa fa-plus me-1"></i>Create New
        </a>
      </div>
    </div>
    <WorkspaceNoticesManagementContainer />

    <div v-if="launchMode" class="alert alert-info d-flex align-items-center">
      <i class="fa fa-info-circle me-2"></i>
      <div>
        <strong>Choose an application to run.</strong>
        Click <em>Run Experiment</em> on any enabled application below. Applications without a
        deployment show no Run button &mdash; open them and add a compute resource under
        <em>Execution</em> first.
      </div>
    </div>

    <div class="card">
      <div class="card-body">
        <!-- Loading state -->
        <div v-if="loading" class="text-center py-4 text-muted">
          <i class="fa fa-spinner fa-spin me-1"></i> Loading applications...
        </div>

        <table v-if="!loading" class="table table-hover table-sm">
          <thead>
            <tr>
              <th style="width: 30px"></th>
              <th>Name</th>
              <th class="text-nowrap">Version</th>
              <th class="text-nowrap">Owner</th>
              <th class="text-nowrap">Description</th>
              <th class="text-nowrap" style="width: 1%">Actions</th>
            </tr>
          </thead>
          <tbody class="align-middle">
            <tr v-if="allApplicationData.length === 0">
              <td colspan="6">
                <div class="table-empty">
                  <i class="fa fa-rocket table-empty__icon"></i>
                  <div class="table-empty__title">No applications available</div>
                  <div class="table-empty__text">
                    Add an application using the <strong>Create New</strong> button above.
                  </div>
                </div>
              </td>
            </tr>
            <tr
              v-for="item in allApplicationData"
              :key="(item.appModule as any).app_module_id"
              style="cursor: pointer"
              @click="navigateToApp(item.appModule)"
            >
              <td @click.stop>
                <a
                  href="#"
                  :title="isFavorite(item.appModule) ? 'Remove from favorites' : 'Add to favorites'"
                  @click.prevent="toggleFavorite(item.appModule)"
                >
                  <i
                    :class="
                      isFavorite(item.appModule)
                        ? 'fa fa-star text-warning'
                        : 'far fa-star text-muted'
                    "
                  ></i>
                </a>
              </td>
              <td>
                <i class="fa fa-cube me-2 text-muted"></i>
                <strong :class="{ 'text-muted': item.disabled }">{{
                  (item.appModule as any).app_module_name
                }}</strong>
              </td>
              <td>
                <span v-if="(item.appModule as any).app_module_version" class="badge bg-secondary">{{
                  (item.appModule as any).app_module_version
                }}</span>
                <span v-else class="text-muted">-</span>
              </td>
              <td>
                <span class="fw-medium text-muted">default-admin</span>
                <span class="badge bg-primary ms-1">Admin</span>
              </td>
              <td class="text-muted">{{ truncate((item.appModule as any).app_module_description, 60) }}</td>
              <td class="text-nowrap" style="width: 1%" @click.stop>
                <div class="d-flex gap-2 justify-content-end flex-nowrap">
                  <a
                    v-if="!item.disabled"
                    :href="runExperimentUrl(item.appModule)"
                    class="btn btn-outline-primary btn-pill"
                    title="Run experiment"
                  >
                    <i class="fa fa-play me-1"></i>Run Experiment
                  </a>
                  <button
                    type="button"
                    class="btn btn-outline-danger btn-pill"
                    title="Delete application"
                    @click="confirmDelete(item.appModule)"
                  >
                    <i class="fa fa-trash me-1"></i>Delete
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
        <div
          v-if="allApplicationData.length > 0"
          class="text-end text-muted"
          style="font-size: 0.75rem; padding: 6px 8px"
        >
          Showing {{ allApplicationData.length }}
        </div>
      </div>
    </div>

    <!-- Delete confirmation modal -->
    <div
      v-if="deleteTarget"
      class="modal d-block"
      tabindex="-1"
      style="background: rgba(0, 0, 0, 0.4)"
    >
      <div class="modal-dialog modal-sm modal-dialog-centered">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Delete Application</h5>
            <button type="button" class="btn-close" @click="deleteTarget = null"></button>
          </div>
          <div class="modal-body">
            <p>
              Are you sure you want to delete <strong>{{ (deleteTarget as any).app_module_name }}</strong
              >?
            </p>
            <p class="text-muted mb-0" style="font-size: 0.8125rem">
              This will also remove its interface and all deployments.
            </p>
          </div>
          <div class="modal-footer">
            <button class="btn btn-sm btn-secondary" @click="deleteTarget = null">Cancel</button>
            <button class="btn btn-sm btn-danger" :disabled="deleting" @click="deleteApplication">
              <i v-if="deleting" class="fa fa-spinner fa-spin me-1"></i>Delete
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onBeforeMount } from "vue";
import { services } from "django-airavata-api";
import PgaLink from "../components/PgaLink.vue";
import WorkspaceNoticesManagementContainer from "../components/notices/WorkspaceNoticesManagementContainer.vue";

const accessibleAppModules = ref<unknown[] | null>(null);
const allApplicationModules = ref<unknown[] | null>(null);
const workspacePreferences = ref<unknown | null>(null);
const loading = ref(true);
const deleteTarget = ref<unknown | null>(null);
const deleting = ref(false);

const accessibleModuleIds = computed<string[]>(() =>
  accessibleAppModules.value
    ? (accessibleAppModules.value as Array<{ app_module_id: string }>).map((a) => a.app_module_id)
    : [],
);

const allApplicationData = computed(() =>
  allApplicationModules.value
    ? (allApplicationModules.value as Array<{ app_module_id: string }>).map((app) => ({
        appModule: app,
        disabled: accessibleModuleIds.value.indexOf(app.app_module_id) < 0,
      }))
    : [],
);

const favoriteApplicationIds = computed<string[]>(() => {
  const prefs = workspacePreferences.value as { application_preferences?: Array<{ favorite: boolean; application_id: string }> } | null;
  if (prefs?.application_preferences) {
    return prefs.application_preferences
      .filter((p) => p.favorite)
      .map((p) => p.application_id);
  }
  return [];
});

const launchMode = computed<boolean>(() => {
  try {
    return new URLSearchParams(window.location.search).get("action") === "launch";
  } catch {
    return false;
  }
});

function editUrl(appModule: unknown) {
  return "/workspace/applications/" + (appModule as { app_module_id: string }).app_module_id + "/";
}

function navigateToApp(appModule: unknown) {
  window.location.href = editUrl(appModule);
}

function runExperimentUrl(appModule: unknown) {
  return "/workspace/applications/" + (appModule as { app_module_id: string }).app_module_id + "/create_experiment";
}

function toggleFavorite(appModule: unknown) {
  const mod = appModule as { app_module_id: string };
  const action = isFavorite(appModule) ? "unfavorite" : "favorite";
  (services.ApplicationModuleService as unknown as Record<string, (_opts: unknown) => Promise<unknown>>)[action]({ lookup: mod.app_module_id })
    .then(() => services.WorkspacePreferencesService.get())
    .then((prefs: unknown) => (workspacePreferences.value = prefs));
}

function isFavorite(appModule: unknown): boolean {
  return favoriteApplicationIds.value.indexOf((appModule as { app_module_id: string }).app_module_id) >= 0;
}

function truncate(text: string | null | undefined, len: number): string {
  if (!text) return "";
  return text.length > len ? text.substring(0, len) + "..." : text;
}

function confirmDelete(appModule: unknown) {
  deleteTarget.value = appModule;
}

function deleteApplication() {
  if (!deleteTarget.value) return;
  deleting.value = true;
  const target = deleteTarget.value as { app_module_id: string };
  services.ApplicationModuleService.delete({ lookup: target.app_module_id })
    .then(() => {
      allApplicationModules.value = (allApplicationModules.value as Array<{ app_module_id: string }> | null)?.filter(
        (m) => m.app_module_id !== target.app_module_id,
      ) ?? null;
      deleteTarget.value = null;
    })
    .catch(() => {
      window.location.href = editUrl(target);
    })
    .finally(() => {
      deleting.value = false;
    });
}

function loadApplications() {
  loading.value = true;
  Promise.all([
    services.ApplicationModuleService.list()
      .then((result: unknown) => (accessibleAppModules.value = result as unknown[]))
      .catch(() => (accessibleAppModules.value = [])),
    services.ApplicationModuleService.listAll()
      .then((result: unknown) => (allApplicationModules.value = result as unknown[]))
      .catch(() => (allApplicationModules.value = [])),
    services.WorkspacePreferencesService.get()
      .then((prefs: unknown) => (workspacePreferences.value = prefs))
      .catch(() => {}),
  ]).finally(() => {
    loading.value = false;
  });
}

onBeforeMount(() => {
  loadApplications();
});
</script>
