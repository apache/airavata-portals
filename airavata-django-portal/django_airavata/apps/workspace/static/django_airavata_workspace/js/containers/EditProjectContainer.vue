<template>
  <div v-if="project">
    <ProjectEditor
      v-model="project"
      @save="saveProject"
      @valid="valid = true"
      @invalid="valid = false"
    >
      <template #buttons>
        <ShareButton :entity-id="projectId" />
      </template>
    </ProjectEditor>
    <div class="d-flex justify-content-end">
      <button class="btn btn-primary btn-sm" :disabled="!valid" @click="saveProject">Save</button>
      <button class="btn btn-secondary btn-sm" @click="cancel">Cancel</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { services } from "django-airavata-api";
import { components } from "django-airavata-common-ui";
import urls from "../utils/urls";
import ProjectEditor from "../components/project/ProjectEditor.vue";

const ShareButton = components.ShareButton;

const props = defineProps<{
  projectId: string;
}>();

const project = ref<unknown>(null);
const valid = ref(false);

onMounted(() => {
  services.ProjectService.retrieve({ lookup: props.projectId }).then(
    (p: unknown) => (project.value = p),
  );
});

function saveProject() {
  if (valid.value) {
    services.ProjectService.update({
      lookup: props.projectId,
      data: project.value,
    }).then(() => {
      urls.navigateToProjectsList();
    });
  }
}

function cancel() {
  urls.navigateToProjectsList();
}
</script>

<style>
/* style the containing div, in base.html template */
.main-content-wrapper {
  background-color: #ffffff;
}
</style>
