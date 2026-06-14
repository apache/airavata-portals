<template>
  <b-form-group label="Project">
    <b-form-select v-model="projectId" required>
      <template #first>
        <option :value="null" disabled>Select a Project</option>
      </template>
      <optgroup label="My Projects">
        <option
          v-for="project in myProjectOptions"
          :value="project.value"
          :key="project.value"
        >
          {{ project.text }}
        </option>
      </optgroup>
      <optgroup label="Projects Shared With Me">
        <option
          v-for="project in sharedProjectOptions"
          :value="project.value"
          :key="project.value"
        >
          {{ project.text }}
        </option>
      </optgroup>
    </b-form-select>
  </b-form-group>
</template>

<script>
import { mapState } from "pinia";
import { useExperimentStore } from "./store";

export default {
  props: {
    value: {
      type: String,
      default: null,
    },
  },
  data() {
    return {
      projectId: this.value,
    };
  },
  async mounted() {
    await useExperimentStore().loadProjects();
  },
  computed: {
    ...mapState(useExperimentStore, ["projects"]),
    sharedProjectOptions: function () {
      return this.projects
        ? this.projects
            .filter((p) => !p.is_owner)
            .map((project) => ({
              value: project.project_id,
              text:
                project.name +
                (!project.is_owner ? " (owned by " + project.owner + ")" : ""),
            }))
        : [];
    },
    myProjectOptions() {
      return this.projects
        ? this.projects
            .filter((p) => p.is_owner)
            .map((project) => ({
              value: project.project_id,
              text: project.name,
            }))
        : [];
    },
  },
  watch: {
    projectId() {
      const inputEvent = new CustomEvent("input", {
        detail: [this.projectId],
        composed: true,
        bubbles: true,
      });
      this.$el.dispatchEvent(inputEvent);
    },
  },
};
</script>

<style lang="scss">
@import "./styles";
:host {
  display: block;
}
</style>
