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

<script>
import store from "./store";
import { mapGetters } from "vuex";

export default {
  props: {
    value: {
      type: String,
      default: null,
    },
  },
  store: store,
  data() {
    return {
      projectId: this.value,
    };
  },
  async mounted() {
    await this.$store.dispatch("loadProjects");
  },
  computed: {
    ...mapGetters(["projects"]),
    sharedProjectOptions: function () {
      return this.projects
        ? this.projects
            .filter((p) => !p.is_owner)
            .map((project) => ({
              value: project.project_id,
              text: project.name + (!project.is_owner ? " (owned by " + project.owner + ")" : ""),
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
