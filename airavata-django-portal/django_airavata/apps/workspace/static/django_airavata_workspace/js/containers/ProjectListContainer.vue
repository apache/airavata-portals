<template>
  <div>
    <div class="row align-items-center mb-3">
      <div class="col">
        <h1 class="h4 mb-0">Projects</h1>
        <p class="text-muted mb-0">
          Organize your experiments into projects for easier management.
        </p>
      </div>
      <div class="col-auto">
        <ProjectButtonNew @new-project="onNewProject" />
      </div>
    </div>
    <div class="row">
      <div class="col">
        <div class="card">
          <div class="card-body">
            <table class="table table-hover table-sm">
              <thead>
                <tr>
                  <th>Name</th>
                  <th class="text-nowrap">Owner</th>
                  <th class="text-nowrap">Creation Time</th>
                  <th class="text-nowrap" style="width: 1%">Actions</th>
                </tr>
              </thead>
              <tbody class="align-middle">
                <tr v-if="!projects || projects.length === 0">
                  <td colspan="4">
                    <div class="table-empty">
                      <i class="fa fa-folder-open table-empty__icon"></i>
                      <div class="table-empty__title">No projects yet</div>
                      <div class="table-empty__text">
                        Create your first project to start organizing experiments.
                      </div>
                    </div>
                  </td>
                </tr>
                <ProjectListItem
                  v-for="project in (projects || []) as Project[]"
                  :key="project.project_id"
                  :project="project"
                  @delete="onDeleteProject"
                />
              </tbody>
            </table>
            <Pager
              v-if="projects && projects.length > 0 && projectsPaginator"
              :paginator="projectsPaginator"
              @next="nextProjects"
              @previous="previousProjects"
            />
          </div>
        </div>
      </div>
    </div>
    <ProjectDeleteModal
      v-if="deleteTarget"
      ref="deleteModal"
      :project-id="(deleteTarget as any).project_id"
      :project-name="(deleteTarget as any).name"
      @delete="confirmDelete"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onBeforeMount, nextTick } from "vue";
import ProjectButtonNew from "../components/project/ProjectButtonNew.vue";
import ProjectListItem from "../components/project/ProjectListItem.vue";
import ProjectDeleteModal from "../components/project/ProjectDeleteModal.vue";

import { services } from "django-airavata-api";
import { components as comps } from "django-airavata-common-ui";

interface Project {
  project_id: string;
  name: string;
  owner?: string;
  creation_time?: string | Date;
  [key: string]: unknown;
}

const Pager = comps.Pager;

const props = withDefaults(defineProps<{
  initialProjectsData?: unknown | null;
}>(), {
  initialProjectsData: undefined,
});

const projectsPaginator = ref<unknown>(null);
const deleteTarget = ref<unknown | null>(null);
const deleteModal = ref<{ show(): void } | null>(null);

const projects = computed<unknown[] | null>(() =>
  projectsPaginator.value ? (projectsPaginator.value as { results: unknown[] }).results : null,
);

function nextProjects() {
  (projectsPaginator.value as { next(): void }).next();
}

function previousProjects() {
  (projectsPaginator.value as { previous(): void }).previous();
}

function onNewProject() {
  services.ProjectService.list().then((result: unknown) => (projectsPaginator.value = result));
}

function onDeleteProject(project: unknown) {
  deleteTarget.value = project;
  nextTick(() => {
    deleteModal.value?.show();
  });
}

async function confirmDelete(projectId: string) {
  try {
    await services.ProjectService.delete({ lookup: projectId });
    deleteTarget.value = null;
    onNewProject();
  } catch (err) {
    console.error("Failed to delete project:", err);
  }
}

onBeforeMount(() => {
  services.ProjectService.list({
    initialData: props.initialProjectsData,
  }).then((result: unknown) => (projectsPaginator.value = result));
});
</script>
