<template>
  <div class="space-y-1.5">
    <label class="text-sm leading-none font-medium select-none">Project</label>
    <select
      v-model="projectId"
      required
      class="h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-xs outline-none transition-[color,box-shadow] focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50 disabled:cursor-not-allowed disabled:opacity-50 dark:bg-input/30"
    >
      <option :value="null" disabled>Select a Project</option>
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
    </select>
  </div>
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
