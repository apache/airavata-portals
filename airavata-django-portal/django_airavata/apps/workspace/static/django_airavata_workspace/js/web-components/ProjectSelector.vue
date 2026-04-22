<template>
  <div class="mb-3" label="Project">
    <select v-model="projectId" class="form-select" required>
      <option :value="null" disabled>Select a Project</option>
      <optgroup label="My Projects">
        <option v-for="project in myProjectOptions" :key="project.value" :value="project.value">
          {{ project.text }}
        </option>
      </optgroup>
      <optgroup label="Projects Shared With Me">
        <option v-for="project in sharedProjectOptions" :key="project.value" :value="project.value">
          {{ project.text }}
        </option>
      </optgroup>
    </select>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, getCurrentInstance } from "vue";
import { useWebComponentsStore } from "django-airavata-common-ui/js/stores/webComponents";

interface Project {
  project_id: string;
  name: string;
  is_owner: boolean;
  owner: string;
}

interface ProjectOption {
  value: string;
  text: string;
}

const props = withDefaults(defineProps<{
  value?: string | null;
}>(), {
  value: null,
});

const webComponentsStore = useWebComponentsStore();

const projectId = ref<string | null>(props.value ?? null);

const projects = computed(() => webComponentsStore.projects as unknown as Project[] | null);

const sharedProjectOptions = computed<ProjectOption[]>(() => {
  return projects.value
    ? projects.value
        .filter((p) => !p.is_owner)
        .map((project) => ({
          value: project.project_id,
          text: project.name + (!project.is_owner ? " (owned by " + project.owner + ")" : ""),
        }))
    : [];
});

const myProjectOptions = computed<ProjectOption[]>(() => {
  return projects.value
    ? projects.value
        .filter((p) => p.is_owner)
        .map((project) => ({
          value: project.project_id,
          text: project.name,
        }))
    : [];
});

watch(projectId, () => {
  const instance = getCurrentInstance();
  const el = instance?.proxy?.$el as Element | undefined;
  if (el) {
    const inputEvent = new CustomEvent("input", {
      detail: [projectId.value],
      composed: true,
      bubbles: true,
    });
    el.dispatchEvent(inputEvent);
  }
});

onMounted(async () => {
  await webComponentsStore.loadProjects();
});
</script>

<style lang="scss">
@import "./styles";
:host {
  display: block;
}
</style>
