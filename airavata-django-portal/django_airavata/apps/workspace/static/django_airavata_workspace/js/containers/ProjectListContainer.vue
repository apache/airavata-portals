<template>
  <div>
    <div class="row align-items-center mb-3">
      <div class="col">
        <h1 class="h4 mb-0">Projects</h1>
        <p class="text-muted mb-0">Organize your experiments into projects for easier management.</p>
      </div>
      <div class="col-auto">
        <project-button-new @new-project="onNewProject" />
      </div>
    </div>
    <div class="row">
      <div class="col">
        <div class="card">
          <div class="card-body">
            <table class="table table-hover">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Owner</th>
                  <th>Creation Time</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                <tr v-if="!projects || projects.length === 0">
                  <td colspan="4">
                    <div class="table-empty">
                      <i class="fa fa-folder-open table-empty__icon"></i>
                      <div class="table-empty__title">No projects yet</div>
                      <div class="table-empty__text">Create your first project to start organizing experiments.</div>
                    </div>
                  </td>
                </tr>
                <project-list-item
                  v-for="project in (projects || [])"
                  :project="project"
                  :key="project.project_id"
                  @delete="onDeleteProject"
                />
              </tbody>
            </table>
            <pager v-if="projects && projects.length > 0"
              v-bind:paginator="projectsPaginator"
              v-on:next="nextProjects"
              v-on:previous="previousProjects"
            ></pager>
          </div>
        </div>
      </div>
    </div>
    <project-delete-modal
      v-if="deleteTarget"
      ref="deleteModal"
      :projectId="deleteTarget.project_id"
      :projectName="deleteTarget.name"
      @delete="confirmDelete"
    />
  </div>
</template>

<script>
import ProjectButtonNew from "../components/project/ProjectButtonNew.vue";
import ProjectListItem from "../components/project/ProjectListItem.vue";
import ProjectDeleteModal from "../components/project/ProjectDeleteModal.vue";

import { services } from "django-airavata-api";
import { components as comps } from "django-airavata-common-ui";

export default {
  props: ["initialProjectsData"],
  name: "project-list-container",
  data() {
    return {
      projectsPaginator: null,
      deleteTarget: null,
    };
  },
  components: {
    "project-list-item": ProjectListItem,
    "project-button-new": ProjectButtonNew,
    "project-delete-modal": ProjectDeleteModal,
    pager: comps.Pager,
  },
  methods: {
    nextProjects: function () {
      this.projectsPaginator.next();
    },
    previousProjects: function () {
      this.projectsPaginator.previous();
    },
    onNewProject: function () {
      services.ProjectService.list().then(
        (result) => (this.projectsPaginator = result)
      );
    },
    onDeleteProject(project) {
      this.deleteTarget = project;
      this.$nextTick(() => {
        this.$refs.deleteModal.show();
      });
    },
    async confirmDelete(projectId) {
      try {
        await services.ProjectService.delete({ lookup: projectId });
        this.deleteTarget = null;
        this.onNewProject(); // Reload list
      } catch (err) {
        console.error("Failed to delete project:", err);
      }
    },
  },
  computed: {
    projects: function () {
      return this.projectsPaginator ? this.projectsPaginator.results : null;
    },
  },
  beforeMount: function () {
    services.ProjectService.list({
      initialData: this.initialProjectsData,
    }).then((result) => (this.projectsPaginator = result));
  },
};
</script>
