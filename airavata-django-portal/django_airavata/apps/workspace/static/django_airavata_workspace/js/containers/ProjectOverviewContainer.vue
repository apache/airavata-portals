<template>
  <div>
    <breadcrumb-nav :crumbs="breadcrumbs" />

    <!-- Inline editable project header -->
    <div class="card mb-3">
      <div class="card-body">
        <div class="row">
          <div class="col-md-8">
            <div class="mb-3">
              <label for="project-name-input" class="form-label small text-muted mb-1">Project Name</label>
              <input
                id="project-name-input"
                type="text"
                class="form-control form-control-lg fw-bold"
                v-model="editName"
                :disabled="!project"
                placeholder="Project name"
              />
            </div>
            <div class="mb-0">
              <label for="project-description-input" class="form-label small text-muted mb-1">Description</label>
              <textarea
                id="project-description-input"
                class="form-control"
                rows="2"
                v-model="editDescription"
                :disabled="!project"
                placeholder="Optional description"
              ></textarea>
            </div>
          </div>
          <div class="col-md-4">
            <div class="mb-2">
              <div class="small text-muted">Owner</div>
              <div>{{ project ? project.owner : "" }}</div>
            </div>
            <div class="mb-2">
              <div class="small text-muted">Created</div>
              <div>{{ formattedCreationTime }}</div>
            </div>
            <div class="mb-0">
              <div class="small text-muted">ID</div>
              <code>{{ projectId }}</code>
            </div>
          </div>
        </div>
        <div class="d-flex justify-content-end mt-3 gap-2">
          <button
            v-if="isDirty"
            class="btn btn-secondary btn-sm"
            @click="resetEdits"
            :disabled="saving"
          >Cancel</button>
          <button
            v-if="isDirty"
            class="btn btn-primary btn-sm"
            @click="saveProject"
            :disabled="saving || !editName || !editName.trim()"
          >
            <i class="fa fa-save me-1"></i>{{ saving ? "Saving…" : "Save" }}
          </button>
          <button class="btn btn-outline-danger btn-sm" @click="showDeleteModal" :disabled="saving">
            <i class="fa fa-trash me-1"></i>Delete
          </button>
        </div>
      </div>
    </div>

    <div class="row">
      <!-- Experiments -->
      <div class="col-md-6 mb-3">
        <div class="card h-100">
          <div class="card-header d-flex justify-content-between align-items-center">
            <span><i class="fa fa-flask me-1"></i>Experiments</span>
            <a :href="experimentsUrl" class="btn btn-link btn-sm p-0">View All</a>
          </div>
          <div class="card-body">
            <div v-if="loadingExperiments" class="text-center py-3">
              <i class="fa fa-spinner fa-spin"></i>
            </div>
            <div v-else-if="!experiments || experiments.length === 0" class="text-center py-3 text-muted">
              <i class="fa fa-flask d-block mb-2" style="font-size: 1.5rem;"></i>
              No experiments yet
            </div>
            <template v-else>
              <div class="list-group list-group-flush">
                <a v-for="exp in experiments" :key="exp.experiment_id"
                  :href="viewExperimentUrl(exp)"
                  class="list-group-item list-group-item-action d-flex justify-content-between align-items-center"
                >
                  <span>{{ exp.name }}</span>
                  <experiment-status-badge :statusName="exp.experiment_status.name" />
                </a>
              </div>
              <pager
                v-if="experimentsPaginator"
                :paginator="experimentsPaginator"
                @next="nextExperiments"
                @previous="previousExperiments"
              />
            </template>
          </div>
          <div class="card-footer">
            <a :href="newExperimentUrl" class="btn btn-primary btn-sm">
              <i class="fa fa-plus me-1"></i>New Experiment
            </a>
          </div>
        </div>
      </div>

      <!-- Artifacts -->
      <div class="col-md-6 mb-3">
        <div class="card h-100">
          <div class="card-header d-flex justify-content-between align-items-center">
            <span><i class="fa fa-database me-1"></i>Artifacts</span>
            <a :href="artifactsUrl" class="btn btn-link btn-sm p-0">View All</a>
          </div>
          <div class="card-body">
            <div v-if="loadingArtifacts" class="text-center py-3">
              <i class="fa fa-spinner fa-spin"></i>
            </div>
            <div v-else-if="!artifacts || artifacts.length === 0" class="text-center py-3 text-muted">
              <i class="fa fa-database d-block mb-2" style="font-size: 1.5rem;"></i>
              No datasets yet
            </div>
            <template v-else>
              <div class="list-group list-group-flush">
                <div v-for="(artifact, idx) in artifacts" :key="artifactKey(artifact, idx)"
                  class="list-group-item d-flex justify-content-between align-items-center"
                >
                  <span class="text-truncate">{{ artifactName(artifact) }}</span>
                  <small class="text-muted ms-2" v-if="artifactDate(artifact)">{{ artifactDate(artifact) }}</small>
                </div>
              </div>
              <div class="pager" v-if="artifactsTotal > 0">
                <span class="pager-element" v-if="artifactsPage > 1">
                  <a href="#" class="action-link" @click.prevent="previousArtifacts">
                    <i class="fa fa-chevron-left" aria-hidden="true"></i> Previous
                  </a>
                </span>
                <span class="pager-element">
                  Showing {{ artifactsFirst }} - {{ artifactsLast }} of {{ artifactsTotal }}
                </span>
                <span class="pager-element" v-if="artifactsLast < artifactsTotal">
                  <a href="#" class="action-link" @click.prevent="nextArtifacts">
                    Next <i class="fa fa-chevron-right" aria-hidden="true"></i>
                  </a>
                </span>
              </div>
            </template>
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
    pager: comps.Pager,
  },
  data() {
    return {
      project: null,
      editName: this.projectName || "",
      editDescription: "",
      saving: false,
      experimentsPaginator: null,
      loadingExperiments: true,
      // Artifacts (client-side pagination)
      allArtifacts: [],
      loadingArtifacts: true,
      artifactsPage: 1,
      artifactsPageSize: 10,
    };
  },
  computed: {
    experimentsUrl() {
      return `/workspace/projects/${encodeURIComponent(this.projectId)}/experiments`;
    },
    artifactsUrl() {
      return `/workspace/projects/${encodeURIComponent(this.projectId)}/artifacts`;
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
    isDirty() {
      if (!this.project) return false;
      const origName = this.project.name || "";
      const origDesc = this.project.description || "";
      return (this.editName || "") !== origName || (this.editDescription || "") !== origDesc;
    },
    experiments() {
      return this.experimentsPaginator ? this.experimentsPaginator.results : null;
    },
    artifactsTotal() {
      return this.allArtifacts ? this.allArtifacts.length : 0;
    },
    artifactsFirst() {
      if (this.artifactsTotal === 0) return 0;
      return (this.artifactsPage - 1) * this.artifactsPageSize + 1;
    },
    artifactsLast() {
      return Math.min(this.artifactsPage * this.artifactsPageSize, this.artifactsTotal);
    },
    artifacts() {
      if (!this.allArtifacts) return [];
      const start = (this.artifactsPage - 1) * this.artifactsPageSize;
      return this.allArtifacts.slice(start, start + this.artifactsPageSize);
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
        window.location.assign("/workspace/projects");
      } catch (err) {
        console.error("Failed to delete project:", err);
      }
    },
    resetEdits() {
      if (this.project) {
        this.editName = this.project.name || "";
        this.editDescription = this.project.description || "";
      }
    },
    async saveProject() {
      if (!this.project || !this.isDirty) return;
      this.saving = true;
      try {
        this.project.name = this.editName;
        this.project.description = this.editDescription;
        await services.ProjectService.update({
          lookup: this.projectId,
          data: this.project,
        });
        // Re-fetch to sync server state
        await this.loadProject();
      } catch (err) {
        console.error("Failed to save project:", err);
      } finally {
        this.saving = false;
      }
    },
    async loadProject() {
      try {
        this.project = await services.ProjectService.retrieve({ lookup: this.projectId });
        this.editName = this.project.name || "";
        this.editDescription = this.project.description || "";
      } catch (err) {
        console.error("Failed to load project:", err);
      }
    },
    async loadExperiments() {
      this.loadingExperiments = true;
      try {
        this.experimentsPaginator = await services.ExperimentSearchService.list({
          PROJECT_ID: this.projectId,
          limit: 10,
        });
      } catch (err) {
        console.error("Failed to load experiments:", err);
        this.experimentsPaginator = null;
      } finally {
        this.loadingExperiments = false;
      }
    },
    async nextExperiments() {
      if (this.experimentsPaginator) {
        await this.experimentsPaginator.next();
      }
    },
    async previousExperiments() {
      if (this.experimentsPaginator) {
        await this.experimentsPaginator.previous();
      }
    },
    async loadArtifacts() {
      this.loadingArtifacts = true;
      try {
        let result = null;
        if (services.DataProductService && services.DataProductService.list) {
          result = await services.DataProductService.list({ "project-id": this.projectId });
        }
        let items = [];
        if (result) {
          if (Array.isArray(result)) {
            items = result;
          } else if (Array.isArray(result.results)) {
            items = result.results;
          }
        }
        // Sort by creation time descending
        items.sort((a, b) => {
          const ta = new Date(this.artifactCreationTime(a) || 0).getTime();
          const tb = new Date(this.artifactCreationTime(b) || 0).getTime();
          return tb - ta;
        });
        this.allArtifacts = items;
        this.artifactsPage = 1;
      } catch (err) {
        console.error("Failed to load artifacts:", err);
        this.allArtifacts = [];
      } finally {
        this.loadingArtifacts = false;
      }
    },
    nextArtifacts() {
      if (this.artifactsLast < this.artifactsTotal) {
        this.artifactsPage += 1;
      }
    },
    previousArtifacts() {
      if (this.artifactsPage > 1) {
        this.artifactsPage -= 1;
      }
    },
    artifactCreationTime(artifact) {
      return artifact.creation_time || artifact.creationTime || null;
    },
    artifactName(artifact) {
      return artifact.product_name || artifact.productName || artifact.name || artifact.product_uri || "Untitled";
    },
    artifactDate(artifact) {
      const t = this.artifactCreationTime(artifact);
      return t ? moment(new Date(t)).fromNow() : "";
    },
    artifactKey(artifact, idx) {
      return artifact.product_uri || artifact.productUri || artifact.id || idx;
    },
  },
  beforeMount() {
    this.loadProject();
    this.loadExperiments();
    this.loadArtifacts();
  },
};
</script>
