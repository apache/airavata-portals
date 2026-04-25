<template>
  <div>
    <breadcrumb-nav :crumbs="breadcrumbs" />

    <!-- Inline editable project header -->
    <div class="card mb-3">
      <div class="card-body">
        <div class="row">
          <div class="col-md-8">
            <div class="mb-3">
              <label for="project-name-input" class="form-label small text-muted mb-1"
                >Project Name</label
              >
              <input
                id="project-name-input"
                v-model="editName"
                type="text"
                class="form-control form-control-lg fw-bold"
                :disabled="!project"
                placeholder="Project name"
              />
            </div>
            <div class="mb-0">
              <label for="project-description-input" class="form-label small text-muted mb-1"
                >Description</label
              >
              <textarea
                id="project-description-input"
                v-model="editDescription"
                class="form-control"
                rows="2"
                :disabled="!project"
                placeholder="Optional description"
              ></textarea>
            </div>
          </div>
          <div class="col-md-4">
            <div class="mb-2">
              <div class="small text-muted">Owner</div>
              <div>{{ project ? (project as Record<string, unknown>).owner : "" }}</div>
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
            :disabled="saving"
            @click="resetEdits"
          >
            Cancel
          </button>
          <button
            v-if="isDirty"
            class="btn btn-primary btn-sm"
            :disabled="saving || !editName || !editName.trim()"
            @click="saveProject"
          >
            <i class="fa fa-save me-1"></i>{{ saving ? "Saving…" : "Save" }}
          </button>
          <button class="btn btn-outline-danger btn-sm" :disabled="saving" @click="showDeleteModal">
            <i class="fa fa-trash me-1"></i>Delete
          </button>
        </div>
      </div>
    </div>

    <project-members-card v-if="project && (project as Record<string, unknown>).project_id" :project="projectTyped!" />

    <project-resources-card v-if="project && (project as Record<string, unknown>).project_id" :project="projectTyped!" />

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
            <div
              v-else-if="!experiments || experiments.length === 0"
              class="text-center py-3 text-muted"
            >
              <i class="fa fa-flask d-block mb-2" style="font-size: 1.5rem"></i>
              No experiments yet
            </div>
            <template v-else>
              <div class="list-group list-group-flush">
                <a
                  v-for="exp in experiments"
                  :key="(exp as Record<string, unknown>).experiment_id as string"
                  :href="viewExperimentUrl(exp as Record<string, unknown>)"
                  class="list-group-item list-group-item-action d-flex justify-content-between align-items-center"
                >
                  <span>{{ (exp as Record<string, unknown>).name }}</span>
                  <experiment-status-badge :status-name="((exp as Record<string, unknown>).experiment_status as Record<string, unknown>).name" />
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
            <div
              v-else-if="!artifacts || artifacts.length === 0"
              class="text-center py-3 text-muted"
            >
              <i class="fa fa-database d-block mb-2" style="font-size: 1.5rem"></i>
              No datasets yet
            </div>
            <template v-else>
              <div class="list-group list-group-flush">
                <div
                  v-for="(artifact, idx) in artifacts"
                  :key="artifactKey(artifact as Record<string, unknown>, idx)"
                  class="list-group-item d-flex justify-content-between align-items-center"
                >
                  <span class="text-truncate">{{ artifactName(artifact as Record<string, unknown>) }}</span>
                  <small v-if="artifactDate(artifact as Record<string, unknown>)" class="text-muted ms-2">{{
                    artifactDate(artifact as Record<string, unknown>)
                  }}</small>
                </div>
              </div>
              <div v-if="artifactsTotal > 0" class="pager">
                <span v-if="artifactsPage > 1" class="pager-element">
                  <a href="#" class="action-link" @click.prevent="previousArtifacts">
                    <i class="fa fa-chevron-left" aria-hidden="true"></i> Previous
                  </a>
                </span>
                <span class="pager-element">
                  Showing {{ artifactsFirst }} - {{ artifactsLast }} of {{ artifactsTotal }}
                </span>
                <span v-if="artifactsLast < artifactsTotal" class="pager-element">
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
      ref="deleteModalRef"
      :project-id="projectId"
      :project-name="(project as Record<string, unknown>).name as string"
      @delete="deleteProject"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onBeforeMount } from "vue";
import { services } from "django-airavata-api";
import { components as comps } from "django-airavata-common-ui";
import { relativeTime } from "django-airavata-common-ui/js/utils/dates.js";
import ProjectDeleteModal from "../components/project/ProjectDeleteModal.vue";
import ProjectMembersCard from "../components/project/ProjectMembersCard.vue";
import ProjectResourcesCard from "../components/project/ProjectResourcesCard.vue";

const BreadcrumbNav = comps.BreadcrumbNav;
const ExperimentStatusBadge = comps.ExperimentStatusBadge;
const Pager = comps.Pager;

const props = withDefaults(defineProps<{
  projectId: string;
  projectName: string;
  breadcrumbs?: unknown[];
}>(), {
  breadcrumbs: () => [],
});

const project = ref<unknown>(null);
const editName = ref(props.projectName || "");
const editDescription = ref("");
const saving = ref(false);
const experimentsPaginator = ref<unknown>(null);
const loadingExperiments = ref(true);
// Artifacts (client-side pagination)
const allArtifacts = ref<unknown[]>([]);
const loadingArtifacts = ref(true);
const artifactsPage = ref(1);
const artifactsPageSize = 10;
const deleteModalRef = ref<InstanceType<typeof ProjectDeleteModal> | null>(null);

interface TypedProject {
  project_id: string;
  owner?: string;
  [key: string]: unknown;
}

const projectTyped = computed<TypedProject | null>(() =>
  project.value ? (project.value as unknown as TypedProject) : null,
);

const experimentsUrl = computed(() =>
  `/workspace/projects/${encodeURIComponent(props.projectId)}/experiments`,
);
const artifactsUrl = computed(() =>
  `/workspace/projects/${encodeURIComponent(props.projectId)}/artifacts`,
);
const newExperimentUrl = "/workspace/launch";

const formattedCreationTime = computed(() => {
  const p = project.value as Record<string, unknown> | null;
  if (p && p.creation_time) {
    return relativeTime(new Date(p.creation_time as string));
  }
  return "";
});

const isDirty = computed(() => {
  const p = project.value as Record<string, unknown> | null;
  if (!p) return false;
  const origName = (p.name as string) || "";
  const origDesc = (p.description as string) || "";
  return (editName.value || "") !== origName || (editDescription.value || "") !== origDesc;
});

const experiments = computed<unknown[] | null>(() => {
  const pag = experimentsPaginator.value as { results: unknown[] } | null;
  return pag ? pag.results : null;
});

const artifactsTotal = computed(() => allArtifacts.value ? allArtifacts.value.length : 0);

const artifactsFirst = computed(() => {
  if (artifactsTotal.value === 0) return 0;
  return (artifactsPage.value - 1) * artifactsPageSize + 1;
});

const artifactsLast = computed(() =>
  Math.min(artifactsPage.value * artifactsPageSize, artifactsTotal.value),
);

const artifacts = computed<unknown[]>(() => {
  if (!allArtifacts.value) return [];
  const start = (artifactsPage.value - 1) * artifactsPageSize;
  return allArtifacts.value.slice(start, start + artifactsPageSize);
});

function viewExperimentUrl(experiment: Record<string, unknown>): string {
  return `/workspace/projects/${encodeURIComponent(props.projectId)}/experiments/${encodeURIComponent(experiment.experiment_id as string)}/`;
}

function showDeleteModal(): void {
  deleteModalRef.value?.show();
}

async function deleteProject(projectId: string): Promise<void> {
  try {
    await services.ProjectService.delete({ lookup: projectId });
    window.location.assign("/workspace/projects");
  } catch (err) {
    console.error("Failed to delete project:", err);
  }
}

function resetEdits(): void {
  const p = project.value as Record<string, unknown> | null;
  if (p) {
    editName.value = (p.name as string) || "";
    editDescription.value = (p.description as string) || "";
  }
}

async function saveProject(): Promise<void> {
  const p = project.value as Record<string, unknown> | null;
  if (!p || !isDirty.value) return;
  saving.value = true;
  try {
    p.name = editName.value;
    p.description = editDescription.value;
    await services.ProjectService.update({
      lookup: props.projectId,
      data: project.value,
    });
    // Re-fetch to sync server state
    await loadProject();
  } catch (err) {
    console.error("Failed to save project:", err);
  } finally {
    saving.value = false;
  }
}

async function loadProject(): Promise<void> {
  try {
    project.value = await services.ProjectService.retrieve({ lookup: props.projectId });
    const p = project.value as Record<string, unknown>;
    editName.value = (p.name as string) || "";
    editDescription.value = (p.description as string) || "";
  } catch (err) {
    console.error("Failed to load project:", err);
  }
}

async function loadExperiments(): Promise<void> {
  loadingExperiments.value = true;
  try {
    experimentsPaginator.value = await services.ExperimentSearchService.list({
      PROJECT_ID: props.projectId,
      limit: 10,
    });
  } catch (err) {
    console.error("Failed to load experiments:", err);
    experimentsPaginator.value = null;
  } finally {
    loadingExperiments.value = false;
  }
}

async function nextExperiments(): Promise<void> {
  const pag = experimentsPaginator.value as { next(): Promise<void> } | null;
  if (pag) {
    await pag.next();
  }
}

async function previousExperiments(): Promise<void> {
  const pag = experimentsPaginator.value as { previous(): Promise<void> } | null;
  if (pag) {
    await pag.previous();
  }
}

function artifactCreationTime(artifact: Record<string, unknown>): string | null {
  return (artifact.creation_time as string) || (artifact.creationTime as string) || null;
}

async function loadArtifacts(): Promise<void> {
  loadingArtifacts.value = true;
  try {
    let result: unknown = null;
    const DataProductService = (services as unknown as Record<string, unknown>).DataProductService as { list?: (_params: unknown) => Promise<unknown> } | undefined;
    if (DataProductService && DataProductService.list) {
      result = await DataProductService.list({ "project-id": props.projectId });
    }
    let items: unknown[] = [];
    if (result) {
      if (Array.isArray(result)) {
        items = result;
      } else {
        const r = result as { results?: unknown[] };
        if (Array.isArray(r.results)) {
          items = r.results;
        }
      }
    }
    // Sort by creation time descending
    (items as Array<Record<string, unknown>>).sort((a, b) => {
      const ta = new Date(artifactCreationTime(a) || 0).getTime();
      const tb = new Date(artifactCreationTime(b) || 0).getTime();
      return tb - ta;
    });
    allArtifacts.value = items;
    artifactsPage.value = 1;
  } catch (err) {
    console.error("Failed to load artifacts:", err);
    allArtifacts.value = [];
  } finally {
    loadingArtifacts.value = false;
  }
}

function nextArtifacts(): void {
  if (artifactsLast.value < artifactsTotal.value) {
    artifactsPage.value += 1;
  }
}

function previousArtifacts(): void {
  if (artifactsPage.value > 1) {
    artifactsPage.value -= 1;
  }
}

function artifactName(artifact: Record<string, unknown>): string {
  return (
    (artifact.product_name as string) ||
    (artifact.productName as string) ||
    (artifact.name as string) ||
    (artifact.product_uri as string) ||
    "Untitled"
  );
}

function artifactDate(artifact: Record<string, unknown>): string {
  const t = artifactCreationTime(artifact);
  return t ? relativeTime(new Date(t)) : "";
}

function artifactKey(artifact: Record<string, unknown>, idx: number): string | number {
  return (artifact.product_uri as string) || (artifact.productUri as string) || (artifact.id as string) || idx;
}

onBeforeMount(() => {
  loadProject();
  loadExperiments();
  loadArtifacts();
});
</script>
