<template>
  <div class="space-y-1.5">
    <label class="text-sm leading-none font-medium select-none">Project</label>
    <select v-model="projectId" required :class="nativeSelectClass">
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
import { NATIVE_SELECT_CLASS } from "../lib/utils";

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
    nativeSelectClass() {
      // Native option-driven select styled to match a shadcn <Input>.
      return NATIVE_SELECT_CLASS;
    },
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
