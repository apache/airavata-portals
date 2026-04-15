<template>
  <div>
    <pga-link />
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
    <workspace-notices-management-container/>

    <div class="card">
      <div class="card-body">
        <!-- Loading state -->
        <div v-if="loading" class="text-center py-4 text-muted">
          <i class="fa fa-spinner fa-spin me-1"></i> Loading applications...
        </div>

        <table class="table table-hover table-sm" v-if="!loading">
          <thead>
            <tr>
              <th style="width:30px;"></th>
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
                  <div class="table-empty__text">Add an application using the <strong>Create New</strong> button above.</div>
                </div>
              </td>
            </tr>
            <tr v-for="item in allApplicationData" :key="item.appModule.app_module_id">
              <td>
                <a href="#" @click.prevent="toggleFavorite(item.appModule)" :title="isFavorite(item.appModule) ? 'Remove from favorites' : 'Add to favorites'">
                  <i :class="isFavorite(item.appModule) ? 'fa fa-star text-warning' : 'far fa-star text-muted'"></i>
                </a>
              </td>
              <td>
                <i class="fa fa-cube me-2 text-muted"></i>
                <a :href="editUrl(item.appModule)" class="text-decoration-none" :class="{ 'text-muted': item.disabled }">
                  <strong>{{ item.appModule.app_module_name }}</strong>
                </a>
              </td>
              <td>
                <span v-if="item.appModule.app_module_version" class="badge bg-secondary">{{ item.appModule.app_module_version }}</span>
                <span v-else class="text-muted">-</span>
              </td>
              <td>
                <span class="fw-medium text-muted">default-admin</span>
                <span class="badge bg-primary ms-1">Admin</span>
              </td>
              <td class="text-muted">{{ truncate(item.appModule.app_module_description, 60) }}</td>
              <td class="text-nowrap" style="width: 1%">
                <div class="d-flex gap-2 justify-content-end flex-nowrap">
                  <a :href="runExperimentUrl(item.appModule)" class="btn btn-outline-primary btn-pill" v-if="!item.disabled" title="Run experiment">
                    <i class="fa fa-play me-1"></i>Run Experiment
                  </a>
                  <button type="button" class="btn btn-outline-danger btn-pill" @click="confirmDelete(item.appModule)" title="Delete application">
                    <i class="fa fa-trash me-1"></i>Delete
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
        <div v-if="allApplicationData.length > 0" class="text-end text-muted" style="font-size:0.75rem; padding: 6px 8px;">Showing {{ allApplicationData.length }}</div>
      </div>
    </div>

    <!-- Delete confirmation modal -->
    <div v-if="deleteTarget" class="modal d-block" tabindex="-1" style="background:rgba(0,0,0,0.4);">
      <div class="modal-dialog modal-sm modal-dialog-centered">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Delete Application</h5>
            <button type="button" class="btn-close" @click="deleteTarget = null"></button>
          </div>
          <div class="modal-body">
            <p>Are you sure you want to delete <strong>{{ deleteTarget.app_module_name }}</strong>?</p>
            <p class="text-muted mb-0" style="font-size:0.8125rem;">This will also remove its interface and all deployments.</p>
          </div>
          <div class="modal-footer">
            <button class="btn btn-sm btn-secondary" @click="deleteTarget = null">Cancel</button>
            <button class="btn btn-sm btn-danger" @click="deleteApplication" :disabled="deleting">
              <i v-if="deleting" class="fa fa-spinner fa-spin me-1"></i>Delete
            </button>
          </div>
        </div>
      </div>
    </div>

  </div>
</template>

<script>
import { services } from "django-airavata-api";
import urls from "../utils/urls";
import PgaLink from "../components/PgaLink";
import WorkspaceNoticesManagementContainer from "../components/notices/WorkspaceNoticesManagementContainer";

export default {
  name: "dashboard-container",
  data() {
    return {
      accessibleAppModules: null,
      allApplicationModules: null,
      workspacePreferences: null,
      loading: true,
      deleteTarget: null,
      deleting: false,
    };
  },
  components: {
    WorkspaceNoticesManagementContainer,
    "pga-link": PgaLink,
  },
  methods: {
    handleAppSelected(appModule) {
      urls.navigateToCreateExperiment(appModule);
    },
    editUrl(appModule) {
      return "/workspace/applications/" + appModule.app_module_id + "/";
    },
    runExperimentUrl(appModule) {
      return "/workspace/applications/" + appModule.app_module_id + "/create_experiment";
    },
    toggleFavorite(appModule) {
      const action = this.isFavorite(appModule) ? "unfavorite" : "favorite";
      services.ApplicationModuleService[action]({ lookup: appModule.app_module_id })
        .then(() => services.WorkspacePreferencesService.get())
        .then((prefs) => (this.workspacePreferences = prefs));
    },
    isFavorite(appModule) {
      return this.favoriteApplicationIds.indexOf(appModule.app_module_id) >= 0;
    },
    truncate(text, len) {
      if (!text) return "";
      return text.length > len ? text.substring(0, len) + "..." : text;
    },
    confirmDelete(appModule) {
      this.deleteTarget = appModule;
    },
    deleteApplication() {
      if (!this.deleteTarget) return;
      this.deleting = true;
      services.ApplicationModuleService.delete({ lookup: this.deleteTarget.app_module_id })
        .then(() => {
          this.allApplicationModules = this.allApplicationModules.filter(
            (m) => m.app_module_id !== this.deleteTarget.app_module_id
          );
          this.deleteTarget = null;
        })
        .catch(() => {
          // If simple delete fails, the admin editor handles cascading delete
          // Redirect there instead
          window.location.href = this.editUrl(this.deleteTarget);
        })
        .finally(() => {
          this.deleting = false;
        });
    },
    loadApplications() {
      this.loading = true;
      Promise.all([
        services.ApplicationModuleService.list()
          .then((result) => (this.accessibleAppModules = result))
          .catch(() => (this.accessibleAppModules = [])),
        services.ApplicationModuleService.listAll()
          .then((result) => (this.allApplicationModules = result))
          .catch(() => (this.allApplicationModules = [])),
        services.WorkspacePreferencesService.get()
          .then((prefs) => (this.workspacePreferences = prefs))
          .catch(() => {}),
      ]).finally(() => {
        this.loading = false;
      });
    },
  },
  computed: {
    accessibleModuleIds() {
      return this.accessibleAppModules
        ? this.accessibleAppModules.map((a) => a.app_module_id)
        : [];
    },
    allApplicationData() {
      return this.allApplicationModules
        ? this.allApplicationModules.map((app) => ({
            appModule: app,
            disabled: this.accessibleModuleIds.indexOf(app.app_module_id) < 0,
          }))
        : [];
    },
    favoriteApplicationIds() {
      if (this.workspacePreferences && this.workspacePreferences.application_preferences) {
        return this.workspacePreferences.application_preferences
          .filter((p) => p.favorite)
          .map((p) => p.application_id);
      }
      return [];
    },
  },
  beforeMount() {
    this.loadApplications();
  },
};
</script>

