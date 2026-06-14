<template>
  <div v-if="project">
    <project-editor
      v-model="project"
      @save="saveProject"
      @valid="valid = true"
      @invalid="valid = false"
    >
      <template #buttons>
        <share-button :entity-id="projectId" />
      </template>
    </project-editor>
    <div class="flex justify-end gap-2">
      <Button @click="saveProject" variant="default" :disabled="!valid"
        >Save</Button
      >
      <Button @click="cancel" variant="secondary">Cancel</Button>
    </div>
  </div>
</template>

<script>
import { services } from "django-airavata-api";
import { components } from "django-airavata-common-ui";
import urls from "../utils/urls";
import ProjectEditor from "../components/project/ProjectEditor.vue";

export default {
  name: "edit-project-container",
  props: {
    projectId: {
      type: String,
      required: true,
    },
  },
  data() {
    return {
      project: null,
      valid: false,
    };
  },
  components: {
    ProjectEditor,
    "share-button": components.ShareButton,
  },
  created() {
    services.ProjectService.retrieve({ lookup: this.projectId }).then(
      (project) => (this.project = project),
    );
  },
  methods: {
    saveProject() {
      if (this.valid) {
        services.ProjectService.update({
          lookup: this.projectId,
          data: this.project,
        }).then(() => {
          urls.navigateToProjectsList();
        });
      }
    },
    cancel() {
      urls.navigateToProjectsList();
    },
  },
};
</script>
<style>
/* style the containing div, in base.html template */
.main-content-wrapper {
  background-color: #ffffff;
}
</style>
