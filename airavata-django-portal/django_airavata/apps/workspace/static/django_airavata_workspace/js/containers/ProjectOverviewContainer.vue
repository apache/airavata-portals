<template>
  <div>
    <breadcrumb-nav :crumbs="breadcrumbs" />

    <div class="row align-items-center mb-3">
      <div class="col">
        <h1 class="h4 mb-0">{{ projectName }}</h1>
        <p v-if="project && project.description" class="text-muted mb-0">{{ project.description }}</p>
      </div>
      <div class="col-auto">
        <a :href="editProjectUrl" class="btn btn-outline-secondary btn-sm">
          <i class="fa fa-cog me-1"></i>Settings
        </a>
        <button class="btn btn-outline-danger btn-sm ms-2" @click="showDeleteModal">
          <i class="fa fa-trash me-1"></i>Delete
        </button>
      </div>
    </div>

    <div class="row">
      <!-- Recent Experiments -->
      <div class="col-md-6 mb-3">
        <div class="card h-100">
          <div class="card-header d-flex justify-content-between align-items-center">
            <span><i class="fa fa-flask me-1"></i>Recent Experiments</span>
            <a :href="experimentsUrl" class="btn btn-link btn-sm p-0">View All</a>
          </div>
          <div class="card-body">
            <div v-if="loadingExperiments" class="text-center py-3">
              <i class="fa fa-spinner fa-spin"></i>
            </div>
            <div v-else-if="recentExperiments.length === 0" class="text-center py-3 text-muted">
              <i class="fa fa-flask d-block mb-2" style="font-size: 1.5rem;"></i>
              No experiments yet
            </div>
            <div v-else class="list-group list-group-flush">
              <a v-for="exp in recentExperiments" :key="exp.experiment_id"
                :href="viewExperimentUrl(exp)"
                class="list-group-item list-group-item-action d-flex justify-content-between align-items-center"
              >
                <span>{{ exp.name }}</span>
                <experiment-status-badge :statusName="exp.experiment_status.name" />
              </a>
            </div>
          </div>
          <div class="card-footer">
            <a :href="newExperimentUrl" class="btn btn-primary btn-sm">
              <i class="fa fa-plus me-1"></i>New Experiment
            </a>
          </div>
        </div>
      </div>

      <!-- Recent Datasets -->
      <div class="col-md-6 mb-3">
        <div class="card h-100">
          <div class="card-header d-flex justify-content-between align-items-center">
            <span><i class="fa fa-database me-1"></i>Recent Datasets</span>
            <a :href="datasetsUrl" class="btn btn-link btn-sm p-0">View All</a>
          </div>
          <div class="card-body">
            <div class="text-center py-3 text-muted">
              <i class="fa fa-database d-block mb-2" style="font-size: 1.5rem;"></i>
              No datasets yet
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Project Info -->
    <div class="row">
      <div class="col">
        <div class="card">
          <div class="card-header"><i class="fa fa-info-circle me-1"></i>Project Info</div>
          <div class="card-body">
            <div v-if="project" class="row">
              <div class="col-sm-4">
                <strong>Owner:</strong> {{ project.owner }}
              </div>
              <div class="col-sm-4">
                <strong>Created:</strong> {{ formattedCreationTime }}
              </div>
              <div class="col-sm-4">
                <strong>ID:</strong> <code>{{ projectId }}</code>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    <project-delete-modal
      v-if="project"
      ref="deleteModal"
      :projectId="projectId"
      :projectName="project.name"
      @delete="deleteProject"
    />
  </div>
</template>

<script>
import { services } from "django-airavata-api";
import { components as comps } from "django-airavata-common-ui";
import moment from "moment";
import ProjectDeleteModal from "../components/project/ProjectDeleteModal.vue";

export default {
  name: "project-overview-container",
  props: {
    projectId: { type: String, required: true },
    projectName: { type: String, required: true },
    breadcrumbs: { type: Array, default: () => [] },
  },
  components: {
    "breadcrumb-nav": comps.BreadcrumbNav,
    "experiment-status-badge": comps.ExperimentStatusBadge,
    "project-delete-modal": ProjectDeleteModal,
  },
  data() {
    return {
      project: null,
      recentExperiments: [],
      loadingExperiments: true,
    };
  },
  computed: {
    experimentsUrl() {
      return `/workspace/projects/${encodeURIComponent(this.projectId)}/experiments`;
    },
    datasetsUrl() {
      return `/workspace/projects/${encodeURIComponent(this.projectId)}/datasets`;
    },
    editProjectUrl() {
      return `/workspace/projects/${encodeURIComponent(this.projectId)}/edit`;
    },
    newExperimentUrl() {
      return "/workspace/applications";
    },
    formattedCreationTime() {
      if (this.project && this.project.creation_time) {
        return moment(new Date(this.project.creation_time)).fromNow();
      }
      return "";
    },
  },
  methods: {
    viewExperimentUrl(experiment) {
      return `/workspace/projects/${encodeURIComponent(this.projectId)}/experiments/${encodeURIComponent(experiment.experiment_id)}/`;
    },
    showDeleteModal() {
      this.$refs.deleteModal.show();
    },
    async deleteProject(projectId) {
      try {
        await services.ProjectService.delete({ lookup: projectId });
        window.location.assign("/workspace/");
      } catch (err) {
        console.error("Failed to delete project:", err);
      }
    },
    async loadProject() {
      try {
        this.project = await services.ProjectService.retrieve({ lookup: this.projectId });
      } catch (err) {
        console.error("Failed to load project:", err);
      }
    },
    async loadRecentExperiments() {
      this.loadingExperiments = true;
      try {
        const result = await services.ProjectService.experiments({ lookup: this.projectId });
        this.recentExperiments = (result || []).slice(0, 5);
      } catch (err) {
        console.error("Failed to load experiments:", err);
        this.recentExperiments = [];
      } finally {
        this.loadingExperiments = false;
      }
    },
  },
  beforeMount() {
    this.loadProject();
    this.loadRecentExperiments();
  },
};
</script>
